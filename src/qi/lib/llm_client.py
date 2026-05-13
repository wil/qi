from typing import Any

import requests


class LLMClient:
    def __init__(
        self, base_url: str, model: str, *, api_key: str | None = None
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key

    def chat(self, messages: list[dict[str, object]], **kwargs: object) -> str:
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
        content = data["choices"][0]["message"]["content"]
        assert isinstance(content, str)
        return content
