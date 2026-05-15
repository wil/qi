"""Run subcommand: process files with the LLM."""

import argparse
import json
import logging

from qi.lib.config import load
from qi.lib.llm_client import LLMClient
from qi.prompts.master import SYSTEM_PROMPT

CHARS_PER_TOKEN = 4
FILE_READ_HEAD_CHARS = 1024


logger = logging.getLogger(__name__)


def handle_response(content: str) -> int:
    if content.startswith("```jsonl"):
        content = content.removeprefix("```jsonl").removesuffix("```").strip()

    try:
        for i, line in enumerate(content.splitlines()):
            data = json.loads(line)
            print(data)
    except json.JSONDecodeError as e:
        logger.error(f"Unable to parse line {i}: {e}")
        logger.error(f"Full response:\n{content}")
        return 1

    return 0


def _build_messages(prompt_message: str, file_paths: list[str]) -> list[dict[str, str]]:
    # work out how many files there are
    files_instruction = ""
    if len(file_paths) == 1:
        files_instruction = (
            f"The following message contains the contents (truncated to {FILE_READ_HEAD_CHARS} chars) of the input file '{file_paths[0]}' "
            "relating to this instruction."
        )
    elif len(file_paths) > 1:
        files_instruction = (
            f"The following {len(file_paths)} messages contain the contents of the input files relating to this instruction:\n" +
            "\n- ".join(file_paths)
        )

    if not prompt_message:
        prompt_message = "Analyse the following."

    prompt_instruction = f"INSTRUCTION: {prompt_message}\n\n" + files_instruction

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt_instruction},
    ]
    for file_path in file_paths:
        try:
            with open(file_path) as f:
                content = f.read()
        except OSError as e:
            logger.error(f"Error reading {file_path}: {e}")
            raise

        messages.append({"role": "user", "content": content[:FILE_READ_HEAD_CHARS]})

    return messages


def run(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="qi",
        description="Process files with the LLM",
    )
    parser.add_argument(
        "-p", "--prompt",
        help="User instruction",
    )
    parser.add_argument(
        "files",
        nargs="*",
        metavar="file",
        help="Files to process",
    )
    parsed = parser.parse_args(argv)

    settings = load()

    if not parsed.files and not parsed.prompt:
        logger.error("No input files or prompt provided.")
        return 1

    try:
        messages = _build_messages(parsed.prompt, parsed.files)
    except Exception as e:
        logger.error(f"Failed to construct messages: {e}")
        return 1

    logger.info(messages)

    client = LLMClient(
        base_url=settings.base_url,
        model=settings.model,
        api_key=settings.api_key,
    )

    try:
        response = client.chat(
            messages,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return 1

    return handle_response(response)
