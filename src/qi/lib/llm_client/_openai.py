import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o"
DEFAULT_BASE_URL = "https://api.openai.com/v1"

class OpenAILLMClient:
    def __init__(
        self, base_url: str, model: str, *, api_key: str | None = None
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key

    def chat(self, messages: list[dict[str, str]], **kwargs: object) -> str:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        body: dict[str, Any] = {"model": self.model, "messages": messages}
        body.update(kwargs)

        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()
        data: Any = resp.json()
        logger.info(f"<<< Response:\n{data}")
        content = data["choices"][0]["message"]["content"]
        assert isinstance(content, str)
        return content
