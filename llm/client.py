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
# Routing and passage selection are short classification-style calls: a smaller model
# is faster, uses fewer tokens and has its own rate-limit quota on Groq.
FAST_MODEL = os.getenv("LLM_FAST_MODEL", "openai/gpt-oss-20b")
FAST_REASONING_EFFORT = os.getenv("LLM_FAST_REASONING_EFFORT", "low")
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1000"))
TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))


@lru_cache(maxsize=1)
def _client() -> Groq:
    return Groq(api_key=os.getenv("GROQ_API_KEY"), timeout=TIMEOUT_SECONDS, max_retries=MAX_RETRIES)


def _with_system(messages: list, system: str) -> list:
    return ([{"role": "system", "content": system}] if system else []) + list(messages)


def _fast_options(model: str) -> dict:
    # gpt-oss models spend tokens on hidden reasoning; low effort keeps quick calls quick.
    if model.startswith("openai/gpt-oss") and FAST_REASONING_EFFORT:
        return {"extra_body": {"reasoning_effort": FAST_REASONING_EFFORT}}
    return {}


def chat(messages: list, system: str = "", json_mode: bool = False, fast: bool = False) -> str:
    """Return the full reply. json_mode asks for one JSON object; fast uses the small model."""
    model = FAST_MODEL if fast else MODEL
    kwargs = {"model": model, "max_tokens": MAX_TOKENS, "messages": _with_system(messages, system),
              **(_fast_options(model) if fast else {})}
    if json_mode:
        try:
            response = _client().chat.completions.create(response_format={"type": "json_object"}, **kwargs)
            return (response.choices[0].message.content or "").strip()
        except BadRequestError:
            # Some models reject response_format; the prompt still asks for JSON.
            logger.warning("JSON mode rejected by %s; retrying without it", model)
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
