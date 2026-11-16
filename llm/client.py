"""Thin wrapper around the Groq chat API.

The client is created lazily so modules can be imported (and tested) without an
API key. Model, timeout and retries are configurable through environment variables.
"""
import logging
import os
from functools import lru_cache

from dotenv import load_dotenv
from groq import BadRequestError, Groq

load_dotenv()
logger = logging.getLogger(__name__)

MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1000"))
TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))


@lru_cache(maxsize=1)
def _client() -> Groq:
    return Groq(api_key=os.getenv("GROQ_API_KEY"), timeout=TIMEOUT_SECONDS, max_retries=MAX_RETRIES)


def _with_system(messages: list, system: str) -> list:
    return ([{"role": "system", "content": system}] if system else []) + list(messages)


def chat(messages: list, system: str = "", json_mode: bool = False) -> str:
    """Return the full reply. json_mode asks the model for a single JSON object."""
    kwargs = {"model": MODEL, "max_tokens": MAX_TOKENS, "messages": _with_system(messages, system)}
    if json_mode:
        try:
            response = _client().chat.completions.create(response_format={"type": "json_object"}, **kwargs)
            return (response.choices[0].message.content or "").strip()
        except BadRequestError:
            # Some models reject response_format; the prompt still asks for JSON.
            logger.warning("JSON mode rejected by %s; retrying without it", MODEL)
    response = _client().chat.completions.create(**kwargs)
    return (response.choices[0].message.content or "").strip()


def chat_stream(messages: list, system: str = ""):
    """Yield response tokens as they arrive (Groq streaming)."""
    stream = _client().chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=_with_system(messages, system),
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
