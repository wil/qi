"""Response handler for LLM JSONL responses and tool execution."""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

ToolMap = dict[str, Any]


def _read_file(path: str, start: int = 0, end: int | None = None) -> str:
    with open(path) as f:
        lines = f.readlines()
    if end is not None:
        lines = lines[start:end]
    elif start > 0:
        lines = lines[start:]
    return "".join(lines)


DEFAULT_TOOLS: ToolMap = {
    "ReadFile": _read_file,
}


def _parse_json_objects(content: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    objects: list[dict[str, Any]] = []
    i = 0
    while i < len(content):
        while i < len(content) and content[i] in ' \t\n\r':
            i += 1
        if i >= len(content):
            break
        obj, pos = decoder.raw_decode(content, i)
        objects.append(obj)
        i = pos
    return objects


def _strip_code_fence(content: str) -> str:
    content = re.sub(r'\A```\w*\n?', '', content)
    content = re.sub(r'\n?```\s*\Z', '', content)
    return content.strip()


def handle_response(
    content: str,
    tool_map: ToolMap | None = None,
) -> int:
    if tool_map is None:
        tool_map = DEFAULT_TOOLS

    content = _strip_code_fence(content)

    try:
        for data in _parse_json_objects(content):
            match data.get("type"):

                case "thought":
                    logger.debug("Thought: %s", data.get("content", ""))

                case "reply":
                    print(data["content"])

                case "call":
                    tool_name = data.get("tool", "")
                    args = data.get("args", {})
                    tool_fn = tool_map.get(tool_name)
                    if tool_fn is None:
                        logger.error(f"Unknown tool: {tool_name}")
                        return 1
                    result = tool_fn(**args)
                    print(result)

                case _:
                    print(data)

    except json.JSONDecodeError as e:
        logger.error(f"Unable to parse JSON: {e}")
        logger.error(f"Full response:\n{content}")
        return 1

    return 0
