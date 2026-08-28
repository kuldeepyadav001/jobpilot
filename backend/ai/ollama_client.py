import httpx
from typing import Optional
from loguru import logger
from core.config import settings


class OllamaClient:
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """
        Sends an inference request to the local Ollama instance.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        timeout_config = httpx.Timeout(180.0, connect=10.0)

        try:
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "").strip()
                else:
                    logger.warning(f"[Ollama] Non-200 status code: {response.status_code} - {response.text}")
                    return None
        except httpx.ConnectError:
            logger.warning(f"[Ollama] Connection failed at {self.base_url}. Check if Ollama container is running.")
            return None
        except Exception as e:
            logger.error(f"[Ollama] Inference error ({type(e).__name__}): {e}")
            return None