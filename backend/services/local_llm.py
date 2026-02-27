import requests
import logging

import os

logger = logging.getLogger("LocalLLM")

OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
OLLAMA_URL = f"http://localhost:{OLLAMA_PORT}/api/generate"

def ask_llm(prompt: str):
    """
    Communicates with local Ollama instance using the Mistral model.
    """
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()["response"]
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        return f"Error connecting to local LLM: {str(e)}"
