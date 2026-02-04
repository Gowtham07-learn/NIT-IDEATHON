# SOP Copilot Backend

## How to start the backend

1. **Create `.env`** (copy from `.env.example`):
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```
   Get a key from https://console.groq.com (do not hardcode; use .env only).

2. **Install dependencies** (from project root or `backend/`):
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

4. **Verify:** Open http://localhost:8000/docs — you must see `GET /health` and `POST /chat`.

## Required environment variables

| Variable        | Required | Description                          |
|----------------|----------|--------------------------------------|
| `GROQ_API_KEY` | Yes      | Groq API key (from console.groq.com) |

## Endpoints

| Method | Path     | Description                                      |
|--------|----------|--------------------------------------------------|
| GET    | /health  | Returns `{ "status": "ok" }`                     |
| POST   | /chat    | Input: `{ "message": "string" }` → `{ "reply": "string" }` |

- All AI replies follow SOP structure (Title, Purpose, Applicable Context, Step-by-Step SOP, Best Practices, Optional Automation).
- On Groq error or missing key, backend returns a safe SOP-style fallback reply (never HTTP 500, never empty).

## Architecture

- **Framework:** FastAPI  
- **LLM:** Groq (llama-3.1-70b-versatile)  
- **Context:** Indian regulatory by default; short, voice-friendly responses.
