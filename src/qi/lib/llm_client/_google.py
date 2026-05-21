import logging
from typing import Any

import requests

from qi.lib.schema import RESPONSE_SCHEMA

logger = logging.getLogger(__name__)


DEFAULT_MODEL = "gemini-flash-latest"
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com"


class GoogleLLMClient:
    def __init__(
        self, base_url: str, model: str, *, api_key: str | None = None
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key

    def chat(self, messages: list[dict[str, str]], **kwargs: object) -> str:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-goog-api-key"] = self.api_key

        contents: list[dict[str, Any]] = []
        system_instruction: dict[str, Any] | None = None

        for msg in messages:
            role = msg["role"]
            if role == "system":
                system_instruction = {"parts": [{"text": msg["content"]}]}
            else:
                contents.append({
                    "role": "model" if role == "assistant" else "user",
                    "parts": [{"text": msg["content"]}],
                })

        body: dict[str, Any] = {"contents": contents}
        if system_instruction is not None:
            body["system_instruction"] = system_instruction

        generation_config: dict[str, Any] = {}
        if "temperature" in kwargs:
            generation_config["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            generation_config["maxOutputTokens"] = kwargs["max_tokens"]
        generation_config["responseMimeType"] = "application/json"
        generation_config["responseSchema"] = RESPONSE_SCHEMA
        body["generationConfig"] = generation_config

        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent"
        logger.info(f">>>>>>>>>>>> Request: POST {url}\n{body}")

        resp = requests.post(url, headers=headers, json=body)
        if not resp.ok:
            logger.error(f"<<<<<<<<<<<< Response: {resp.status_code} {resp.reason}\n{resp.text}")
            resp.raise_for_status()
        data: Any = resp.json()
        logger.info(f"<<<<<<<<<<<< Response:\n{data}")
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        assert isinstance(content, str)
        return content
