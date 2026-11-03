"""GJ AI switchboard: one call, several AI providers, automatic fallback.

The tutor builds its messages in OpenAI "Responses" style:
    {"role": "user" | "assistant", "content": "text"}
    {"role": "user", "content": [{"type": "input_text", "text": ...},
                                 {"type": "input_image", "image_url": "data:image/png;base64,..."}]}
This module converts them for each provider and tries providers in order until one answers.
Keys and models come from Streamlit Secrets; a provider with no key is skipped.
"""
import base64

DEFAULT_ORDER = "openai,anthropic,gemini"
DEFAULT_MODELS = {
    "openai": "gpt-5.4-mini",
    "anthropic": "claude-haiku-5-5",
    "gemini": "gemini-flash-latest",
}
KEY_NAMES = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY"}
MODEL_NAMES = {"openai": "OPENAI_MODEL", "anthropic": "ANTHROPIC_MODEL", "gemini": "GEMINI_MODEL"}
LABELS = {"openai": "OpenAI", "anthropic": "Claude", "gemini": "Gemini"}


class AllProvidersFailed(Exception):
    """Raised when no configured provider could answer."""


def configured(setting):
    """Providers that have a key, in the order set by AI_ORDER."""
    order = [p.strip().lower() for p in str(setting("AI_ORDER", DEFAULT_ORDER)).split(",")]
    return [p for p in order if p in KEY_NAMES and setting(KEY_NAMES[p])]


def _parts(content):
    """Yield ("text", str) and ("image", (media_type, raw_bytes)) from one message's content."""
    if isinstance(content, str):
        yield "text", content
        return
    for block in content:
        if block.get("type") in ("input_text", "text"):
            yield "text", block.get("text", "")
        elif block.get("type") == "input_image":
            url = block.get("image_url", "")
            header, _, data = url.partition(",")
            media = header.removeprefix("data:").split(";")[0] or "image/png"
            yield "image", (media, base64.b64decode(data))


def _openai(key, model, instructions, messages, max_tokens):
    import openai
    client = openai.OpenAI(api_key=key, timeout=45.0, max_retries=0)
    response = client.responses.create(
        model=model, max_output_tokens=max_tokens, reasoning={"effort": "low"},
        instructions=instructions, input=messages, store=False,
    )
    return response.output_text or "", response.status == "incomplete"


def _anthropic(key, model, instructions, messages, max_tokens):
    import anthropic
    converted = []
    for m in messages:
        blocks = []
        for kind, value in _parts(m["content"]):
            if kind == "text" and value.strip():
                blocks.append({"type": "text", "text": value})
            elif kind == "image":
                media, raw = value
                blocks.append({"type": "image", "source": {"type": "base64", "media_type": media,
                                                           "data": base64.b64encode(raw).decode("ascii")}})
        if blocks:
            converted.append({"role": m["role"], "content": blocks})
    client = anthropic.Anthropic(api_key=key, timeout=45.0, max_retries=0)
    response = client.messages.create(model=model, max_tokens=max_tokens, system=instructions, messages=converted)
    text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
    return text, response.stop_reason == "max_tokens"


def _gemini(key, model, instructions, messages, max_tokens):
    from google import genai
    from google.genai import types
    contents = []
    for m in messages:
        parts = []
        for kind, value in _parts(m["content"]):
            if kind == "text" and value.strip():
                parts.append(types.Part.from_text(text=value))
            elif kind == "image":
                media, raw = value
                parts.append(types.Part.from_bytes(data=raw, mime_type=media))
        if parts:
            contents.append(types.Content(role="model" if m["role"] == "assistant" else "user", parts=parts))
    client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=45_000))
    response = client.models.generate_content(
        model=model, contents=contents,
        config=types.GenerateContentConfig(system_instruction=instructions, max_output_tokens=max_tokens),
    )
    finish = ""
    if response.candidates:
        finish = str(getattr(response.candidates[0], "finish_reason", "") or "")
    return response.text or "", "MAX_TOKENS" in finish


CALLERS = {"openai": _openai, "anthropic": _anthropic, "gemini": _gemini}


def ask(setting, instructions, messages, max_tokens=1800, only=None):
    """Return (answer_text, provider, incomplete). Tries each configured provider in turn.

    `only` forces one provider (used for side-by-side comparisons)."""
    providers = [only] if only else configured(setting)
    if not providers:
        raise AllProvidersFailed("No AI provider key is configured.")
    errors = []
    for provider in providers:
        key = setting(KEY_NAMES[provider])
        if not key:
            errors.append(f"{LABELS[provider]}: no key")
            continue
        model = str(setting(MODEL_NAMES[provider], DEFAULT_MODELS[provider]))
        try:
            text, incomplete = CALLERS[provider](key, model, instructions, messages, max_tokens)
            if text.strip():
                return text, provider, incomplete
            errors.append(f"{LABELS[provider]}: empty answer")
        except Exception as exc:  # any failure moves on to the next provider
            errors.append(f"{LABELS[provider]}: {type(exc).__name__}")
    raise AllProvidersFailed("; ".join(errors))
