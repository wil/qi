from unittest.mock import Mock, patch

import requests

from qi.lib.llm_client import LLMClient
from qi.lib.llm_client._google import GoogleLLMClient
from qi.lib.llm_client._openai import OpenAILLMClient


def test_chat_returns_content() -> None:
    mock_resp = Mock(spec=requests.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Hello!"}}]
    }

    with patch("qi.lib.llm_client._openai.requests.post", return_value=mock_resp):
        client = LLMClient.create(
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

    with patch("qi.lib.llm_client._openai.requests.post", return_value=mock_resp) as mock_post:
        client = LLMClient.create(
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


def test_google_chat_returns_content() -> None:
    mock_resp = Mock(spec=requests.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "AI learns patterns"}]}}],
    }

    with patch("qi.lib.llm_client._google.requests.post", return_value=mock_resp) as mock_post:
        client = LLMClient.create(
            base_url="https://generativelanguage.googleapis.com",
            model="gemini-flash-latest",
            api_key="goog-key",
        )
        result = client.chat([{"role": "user", "content": "Explain AI"}])

    assert result == "AI learns patterns"
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["headers"]["X-goog-api-key"] == "goog-key"
    assert call_kwargs["json"]["contents"] == [
        {"role": "user", "parts": [{"text": "Explain AI"}]}
    ]


def test_google_chat_system_instruction() -> None:
    mock_resp = Mock(spec=requests.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "OK"}]}}],
    }

    with patch("qi.lib.llm_client._google.requests.post", return_value=mock_resp) as mock_post:
        client = LLMClient.create(
            base_url="https://generativelanguage.googleapis.com",
            model="gemini-flash-latest",
            api_key="goog-key",
        )
        client.chat([
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "Hello"},
        ])

    body = mock_post.call_args.kwargs["json"]
    assert body["system_instruction"] == {"parts": [{"text": "Be concise."}]}
    assert body["contents"] == [
        {"role": "user", "parts": [{"text": "Hello"}]}
    ]


def test_google_chat_maps_generation_config() -> None:
    mock_resp = Mock(spec=requests.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "OK"}]}}],
    }

    with patch("qi.lib.llm_client._google.requests.post", return_value=mock_resp) as mock_post:
        client = LLMClient.create(
            base_url="https://generativelanguage.googleapis.com",
            model="gemini-flash-latest",
            api_key="goog-key",
        )
        client.chat(
            [{"role": "user", "content": "Hi"}],
            temperature=0.5,
            max_tokens=200,
        )

    body = mock_post.call_args.kwargs["json"]
    gc = body["generationConfig"]
    assert gc["temperature"] == 0.5
    assert gc["maxOutputTokens"] == 200
    assert gc["responseMimeType"] == "application/json"
    assert "responseSchema" in gc


def test_factory_returns_openai_client() -> None:
    client = LLMClient.create(
        base_url="https://api.openai.com/v1",
        model="gpt-4o",
    )
    assert isinstance(client, OpenAILLMClient)


def test_factory_returns_google_client() -> None:
    client = LLMClient.create(
        base_url="https://generativelanguage.googleapis.com",
        model="gemini-flash-latest",
        api_key="goog-key",
    )
    assert isinstance(client, GoogleLLMClient)


def test_factory_detects_google_without_scheme() -> None:
    client = LLMClient.create(
        base_url="generativelanguage.googleapis.com",
        model="gemini-flash-latest",
    )
    assert isinstance(client, GoogleLLMClient)
