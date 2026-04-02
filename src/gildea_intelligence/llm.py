"""LLM wrapper — thin layer over the Anthropic SDK with Vertex AI support."""

from __future__ import annotations

import os

import anthropic


_client = None

# Model name mapping: Vertex uses a different format
_VERTEX_MODEL_MAP = {
    "claude-opus-4-0": "claude-opus-4-6",
}

_use_vertex = False


def get_client():
    global _client, _use_vertex
    if _client is not None:
        return _client

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    region = os.environ.get("GOOGLE_CLOUD_REGION", "us-east5")

    if api_key:
        _client = anthropic.Anthropic(api_key=api_key)
        _use_vertex = False
    elif project:
        _client = anthropic.AnthropicVertex(project_id=project, region=region)
        _use_vertex = True
    else:
        raise RuntimeError(
            "No LLM credentials found. Set either:\n"
            "  ANTHROPIC_API_KEY — for direct Anthropic API\n"
            "  GOOGLE_CLOUD_PROJECT — for Vertex AI (with gcloud auth)"
        )

    return _client


def _resolve_model(model: str) -> str:
    """Map model name to Vertex format if using Vertex AI."""
    if _use_vertex:
        return _VERTEX_MODEL_MAP.get(model, model)
    return model


def call(
    prompt: str,
    *,
    system: str = "",
    model: str = "claude-opus-4-0",
    max_tokens: int = 4096,
    temperature: float = 0.0,
) -> str:
    """Single LLM call. Returns the text response."""
    client = get_client()  # must run first to set _use_vertex flag
    messages = [{"role": "user", "content": prompt}]
    kwargs: dict = dict(
        model=_resolve_model(model),
        max_tokens=max_tokens,
        messages=messages,
        temperature=temperature,
    )
    if system:
        kwargs["system"] = system
    response = client.messages.create(**kwargs)
    return response.content[0].text
