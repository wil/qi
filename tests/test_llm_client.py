from unittest.mock import Mock, patch

import requests

from qi.lib.llm_client import LLMClient


def test_chat_returns_content() -> None:
    mock_resp = Mock(spec=requests.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Hello!"}}]
    }

    with patch("qi.lib.llm_client.requests.post", return_value=mock_resp):
        client = LLMClient(
            base_url="https://api.openai.com/v1",
            model="gpt-4o",
        )
        result = client.chat([{"role": "user", "content": "Hi"}])

    assert result == "Hello!"


def test_chat_passes_temperature_and_max_tokens() -> None:
    mock_resp = Mock(spec=requests.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Hello!"}}]
    }

    with patch("qi.lib.llm_client.requests.post", return_value=mock_resp) as mock_post:
        client = LLMClient(
            base_url="https://api.openai.com/v1",
            model="gpt-4o",
            api_key="sk-test",
        )
        client.chat(
            [{"role": "user", "content": "Hi"}],
            temperature=0.7,
            max_tokens=100,
        )

    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["json"]["temperature"] == 0.7
    assert call_kwargs["json"]["max_tokens"] == 100
