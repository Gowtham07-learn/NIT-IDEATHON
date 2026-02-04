"""
SOP Copilot Backend - Groq API.
POST /chat        → text question
POST /chat/image  → screenshot → OCR → AI answer
"""

import os
import re
import io
import logging
from pathlib import Path
from typing import Optional, Tuple

from fastapi import FastAPI, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
from PIL import Image

# OCR imports
import pytesseract
import cv2
import numpy as np

# --------------------------------------------------
# ENV + LOGGING
# --------------------------------------------------
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# TESSERACT PATH (Windows) – set before any pytesseract call
# --------------------------------------------------
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --------------------------------------------------
# FASTAPI APP
# --------------------------------------------------
app = FastAPI(title="SOP Copilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "chrome-extension://*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# PROMPTS
# --------------------------------------------------
SOP_SYSTEM_PROMPT = """You are a Policy & SOP assistant.

Rules:
1. Answer ONLY the user's question.
2. Do NOT output unrelated SOPs.
3. Use this structure:
   - Title
   - Purpose
   - Applicable Context
   - Step-by-Step SOP (numbered)
   - Best Practices
   - Optional Automation / Tooling
4. Assume Indian regulatory context.
5. Be concise and formal.
"""

SOP_FALLBACK = """**Title:** SOP Copilot – Temporary Guidance

**Purpose:** Provide guidance when the AI service is unavailable.

**Applicable Context:** Indian regulatory and operational use.

**Step-by-Step SOP:**
1. Retry your question.
2. Ensure GROQ_API_KEY is set.
3. Check backend at http://localhost:8000/health

**Best Practices:**
- Ask specific questions.
- Use short sentences.

**Optional Automation / Tooling:**
- GET http://localhost:8000/health
"""

WEB_GROUNDED_SYSTEM = """You are a web-grounded Policy & SOP assistant.
The following text is extracted from the currently open web page.
Use ONLY this content to answer the user's question.
If the answer cannot be found in the page, say:
"The provided page does not contain this information."

Rules:
- Do NOT hallucinate. Do NOT use general knowledge.
- Answer concisely and professionally.
- Quote or paraphrase from the page where relevant.
- Use structure: Title, Purpose, Applicable Context, Step-by-Step SOP, Best Practices, Optional Automation / Tooling."""

OCR_IMAGE_SYSTEM = """You are a Policy & SOP assistant.
The user's question was extracted from an uploaded image using OCR.
Answer the question clearly and professionally.
If the question is unclear, ask for clarification.
Use structure: Title, Purpose, Applicable Context, Step-by-Step SOP, Best Practices, Optional Automation / Tooling."""

# --------------------------------------------------
# MODELS
# --------------------------------------------------
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


# --------------------------------------------------
# LLM CALL
# --------------------------------------------------
OCR_FAILURE_MSG = "No readable text found in image. Please upload a clearer screenshot."


def _get_reply_from_groq(
    message: str,
    *,
    page_context: Optional[str] = None,
    ocr_mode: bool = False,
) -> Optional[str]:
    """Call Groq LLM. Returns None only on failure (missing key, exception, empty reply)."""
    message = (message or "").strip()
    if not message:
        logger.warning("Empty message sent to LLM - skipping call")
        return None

    api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not api_key:
        logger.error("USING FALLBACK: GROQ_API_KEY not detected in environment")
        return None

    logger.info("GROQ_API_KEY detected, message length=%d", len(message))

    if ocr_mode:
        system_content = OCR_IMAGE_SYSTEM
    elif page_context and page_context.strip():
        system_content = (
            WEB_GROUNDED_SYSTEM
            + "\n\nPAGE CONTENT:\n"
            + page_context.strip()
            + "\n"
        )
    else:
        system_content = SOP_SYSTEM_PROMPT

    try:
        logger.info("LLM CALLED WITH MESSAGE LENGTH: %d", len(message))
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": message},
            ],
            max_tokens=1024,
        )

        reply = (response.choices[0].message.content or "").strip()
        if reply:
            logger.info("LLM success, reply length=%d", len(reply))
            return reply
        logger.warning("LLM returned empty content - USING FALLBACK")
        return None

    except Exception as e:
        logger.exception("USING FALLBACK: LLM call failed: %s", e)
        return None


def _parse_web_grounded(raw: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (page_content, user_question) if web-grounded format, else (None, None)."""
    m1 = "__SOP_PAGE_CONTEXT__"
    m2 = "__SOP_USER_QUESTION__"
    if m1 not in raw or m2 not in raw:
        return None, None
    try:
        after_m1 = raw.split(m1, 1)[1]
        before_m2, after_m2 = after_m1.split(m2, 1)
        page_content = before_m2.strip()
        user_question = after_m2.strip()
        return page_content, user_question
    except (IndexError, ValueError):
        return None, None


def _extract_question_from_ocr(ocr_text: str) -> str:
    """Extract primary question from OCR output. Filter placeholders; prefer interrogative sentences."""
    if not ocr_text or not ocr_text.strip():
        return ""
    text = ocr_text.strip()
    placeholders = {
        "answer", "type your question", "ask a question", "enter your question",
        "ask something", "type here", "placeholder", "search", "submit", "send",
        "type your question here", "ask a policy or sop question", "write your message",
    }
    lines = [ln.strip() for ln in re.split(r"[\n.!?]+", text) if ln.strip()]
    questions = []
    for ln in lines:
        ln_lower = ln.lower()
        if ln_lower in placeholders or len(ln) < 4:
            continue
        if re.search(r"\b(what|how|why|when|where|which|who|can|could|does|is|are)\b", ln_lower):
            questions.append(ln)
    if questions:
        return " ".join(questions).strip()
    return text


# --------------------------------------------------
# OCR (screenshot-ready: contrast, Otsu, PSM 6/11, Windows path)
# --------------------------------------------------
def _ocr_image(image_bytes: bytes) -> Optional[str]:
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_np = np.array(img)

        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

        # Contrast (helps dark UI / low contrast screenshots)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        _, thresh = cv2.threshold(
            gray, 0, 255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        if np.mean(thresh) > 127:
            thresh = cv2.bitwise_not(thresh)

        for psm in (6, 11):
            raw = pytesseract.image_to_string(thresh, config=f"--psm {psm}")
            logger.info("OCR RAW (psm=%d): %r", psm, raw[:300] + ("..." if len(raw) > 300 else ""))
            if raw and raw.strip():
                break
        else:
            raw = ""

        if not raw or not raw.strip():
            logger.warning("OCR FAILED: no readable text (tried psm 6 and 11)")
            return None

        cleaned = re.sub(r"\s+", " ", raw).strip()
        cleaned = re.sub(r" +", " ", cleaned)
        if not cleaned:
            logger.warning("OCR FAILED: extracted text is empty after normalization")
            return None
        logger.info("OCR SUCCESS: extracted %d chars", len(cleaned))
        return cleaned

    except Exception as e:
        logger.exception("OCR FAILED: %s", e)
        return None


# --------------------------------------------------
# ROUTES
# --------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, req: ChatRequest):
    raw = (req.message or "").strip()
    if not raw:
        return ChatResponse(reply=SOP_FALLBACK)

    page_content, user_question = _parse_web_grounded(raw)
    if page_content is not None and user_question is not None:
        if not page_content or len(page_content) < 20:
            return ChatResponse(
                reply="The page content could not be extracted or is too short. Please ensure the page has readable text and try again."
            )
        reply = _get_reply_from_groq(user_question, page_context=page_content)
    else:
        reply = _get_reply_from_groq(raw)

    return ChatResponse(reply=reply or SOP_FALLBACK)


@app.post("/chat/image", response_model=ChatResponse)
async def chat_image(image: UploadFile = File(..., alias="image")):
    if not image.content_type or not image.content_type.startswith("image/"):
        return ChatResponse(reply="Please upload a valid image file.")

    data = await image.read()
    text = _ocr_image(data)

    # Path 1: OCR failure – return OCR-specific error (never SOP fallback)
    if not text or not text.strip():
        logger.warning("USING OCR FAILURE RESPONSE: no text extracted")
        return ChatResponse(reply=OCR_FAILURE_MSG)

    # OCR succeeded – normalize and extract question
    text = text.strip()
    text = re.sub(r"\s+", " ", text).strip()
    question = _extract_question_from_ocr(text)
    user_message = question.strip() if question else text

    if not user_message:
        logger.warning("USING OCR FAILURE RESPONSE: extracted text filtered to empty")
        return ChatResponse(reply=OCR_FAILURE_MSG)

    logger.info("OCR TEXT PASSED TO AI: %s", user_message[:500] + ("..." if len(user_message) > 500 else ""))

    # Path 2: AI call – ALWAYS attempt when OCR text exists
    api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not api_key:
        logger.error("USING FALLBACK: GROQ_API_KEY not set (OCR succeeded, AI unavailable)")
        return ChatResponse(reply=SOP_FALLBACK)

    reply = _get_reply_from_groq(user_message, ocr_mode=True)

    # Path 3: AI failure (exception, empty) – SOP fallback
    if not reply:
        logger.error("USING FALLBACK: LLM call failed or returned empty (OCR succeeded)")
        return ChatResponse(reply=SOP_FALLBACK)

    return ChatResponse(reply=reply)


# --------------------------------------------------
# RUN
# --------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
