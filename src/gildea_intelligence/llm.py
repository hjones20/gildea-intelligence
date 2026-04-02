"""LLM wrapper — thin layer over the Anthropic SDK."""

from __future__ import annotations

import os

import anthropic


_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client


def call(
    prompt: str,
    *,
    system: str = "",
    model: str = "claude-opus-4-0",
    max_tokens: int = 4096,
    temperature: float = 0.0,
) -> str:
    """Single LLM call. Returns the text response."""
    messages = [{"role": "user", "content": prompt}]
    kwargs: dict = dict(
        model=model,
        max_tokens=max_tokens,
        messages=messages,
        temperature=temperature,
    )
    if system:
        kwargs["system"] = system
    response = get_client().messages.create(**kwargs)
    return response.content[0].text
