"""Listen feature: turn a tutor answer into speakable text, then play it.

Two voices:
- the device's own voice (browser speech, free, instant, works offline once loaded);
- the GJ cloned voices (Gopal / Neetu) from the private RunPod voice service.
"""
import base64
import hashlib
import json
import re
import time

import requests

VOICE_IDS = {("Gopal", "en"): "gopal-en-a", ("Gopal", "hi"): "gopal-hi",
             ("Neetu", "en"): "neetu-en", ("Neetu", "hi"): "neetu-hi"}

_GREEK = {"alpha": "alpha", "beta": "beta", "gamma": "gamma", "delta": "delta", "theta": "theta",
          "lambda": "lambda", "mu": "mu", "pi": "pi", "sigma": "sigma", "omega": "omega", "Delta": "delta"}
_SYMBOLS = [
    (r"\\times", " times "), (r"\\cdot", " times "), (r"\\div", " divided by "), (r"\\pm", " plus or minus "),
    (r"\\leq?", " less than or equal to "), (r"\\geq?", " greater than or equal to "), (r"\\neq", " not equal to "),
    (r"\\approx", " approximately "), (r"\\infty", " infinity "), (r"\\%", " percent"), (r"\\rightarrow|\\to", " gives "),
    (r"\\int", " the integral of "), (r"\\sum", " the sum of "), (r"\\Rightarrow", " so "), (r"\\therefore", " therefore "),
]


def _maths(expr):
    """Read one LaTeX expression aloud in plain English."""
    e = expr
    e = re.sub(r"\\begin\{[a-z*]+\}|\\end\{[a-z*]+\}", " ", e)
    e = e.replace("&", " ").replace("\\\\", ". ")
    e = re.sub(r"\\(?:text|mathrm|textbf|operatorname)\{([^{}]*)\}", r" \1 ", e)
    e = re.sub(r"\\left|\\right|\\,|\\;|\\!|\\quad|\\qquad", " ", e)
    for _ in range(4):  # nested fractions and roots
        e = re.sub(r"\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}", r" (\1) over (\2) ", e)
        e = re.sub(r"\\sqrt\{([^{}]*)\}", r" the square root of (\1) ", e)
    e = re.sub(r"\^\{?2\}?", " squared ", e)
    e = re.sub(r"\^\{?3\}?", " cubed ", e)
    e = re.sub(r"\^\{([^{}]*)\}|\^(\w)", lambda m: f" to the power {m.group(1) or m.group(2)} ", e)
    e = re.sub(r"_\{([^{}]*)\}|_(\w)", lambda m: f" {m.group(1) or m.group(2)} ", e)
    for pattern, words in _SYMBOLS:
        e = re.sub(pattern, words, e)
    e = re.sub(r"\\(" + "|".join(_GREEK) + r")\b", lambda m: f" {_GREEK[m.group(1)]} ", e)
    e = re.sub(r"\\[a-zA-Z]+", " ", e)  # any other command
    e = e.replace("{", " ").replace("}", " ")
    e = re.sub(r"(?<=\w)'(?=\()", " dash ", e)  # f'(x)
    e = e.replace("=", " equals ").replace("+", " plus ").replace("<", " less than ").replace(">", " greater than ")
    e = re.sub(r"(?<=[\s(\d])-(?=[\s\d(a-z])", " minus ", e)
    e = e.replace("(", " ").replace(")", " ")
    return re.sub(r"\s+", " ", e).strip()


def speech_text(markdown):
    """Plain speakable text from a tutor answer (Markdown + LaTeX)."""
    t = re.sub(r"\$\$(.+?)\$\$", lambda m: ". " + _maths(m.group(1)) + ". ", markdown, flags=re.S)
    t = re.sub(r"\$(.+?)\$", lambda m: _maths(m.group(1)), t)
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)          # links: keep the words
    t = re.sub(r"^\s{0,3}#{1,6}\s*", "", t, flags=re.M)      # headings
    t = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", t, flags=re.M)  # list markers
    t = re.sub(r"[*_`|>#]+", " ", t)
    t = re.sub(r"\n{2,}", ". ", t).replace("\n", " ")
    t = re.sub(r"\s+([.,;:!?])", r"\1", t)
    t = re.sub(r"(?:\.\s*){2,}", ". ", t)
    return re.sub(r"\s+", " ", t).strip(" .") + "."


def language_of(text):
    """'hi' when the answer is mostly Devanagari, else 'en'."""
    letters = [c for c in text if c.isalpha()]
    deva = sum(1 for c in letters if "\u0900" <= c <= "\u097f")
    return "hi" if letters and deva / len(letters) > 0.3 else "en"


def browser_voice_html(text, language):
    """A small 'Listen' button that uses the device's own voice (no cost, instant)."""
    lang = "hi-IN" if language == "hi" else "en-IN"
    # Escape <, > and & so answer text can never close the script tag (answers come from an AI model).
    payload = json.dumps(text).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f"""
<div style="font-family:sans-serif">
<button id="b" style="padding:6px 12px;border-radius:8px;border:1px solid #bbb;background:#fff;cursor:pointer">🔊 Listen (device voice)</button>
<script>
const text = {payload};
const btn = document.getElementById('b');
btn.onclick = () => {{
  const s = window.speechSynthesis;
  if (!s) {{ btn.textContent = 'Listening is not supported in this browser'; return; }}
  if (s.speaking) {{ s.cancel(); btn.textContent = '🔊 Listen (device voice)'; return; }}
  const u = new SpeechSynthesisUtterance(text);
  u.lang = '{lang}';
  const v = s.getVoices().find(v => v.lang === '{lang}') || s.getVoices().find(v => v.lang.startsWith('{lang[:2]}'));
  if (v) u.voice = v;
  u.rate = 0.95;
  u.onend = () => btn.textContent = '🔊 Listen (device voice)';
  btn.textContent = '⏹ Stop';
  s.speak(u);
}};
</script></div>"""


class VoiceServiceError(Exception):
    pass


def cloned_voice_mp3(text, voice_id, api_key, endpoint_id, wait_seconds=180):
    """Ask the private RunPod voice service for MP3 audio. Returns bytes."""
    base = f"https://api.runpod.ai/v2/{endpoint_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    body = {"input": {"text": text[:3000], "voice": voice_id}}
    deadline = time.monotonic() + wait_seconds
    reply = requests.post(f"{base}/runsync", json=body, headers=headers, timeout=95).json()
    while reply.get("status") in ("IN_QUEUE", "IN_PROGRESS") and time.monotonic() < deadline:
        time.sleep(3)  # a cold start can take a minute or two
        reply = requests.get(f"{base}/status/{reply['id']}", headers=headers, timeout=30).json()
    if reply.get("status") != "COMPLETED":
        raise VoiceServiceError(reply.get("error") or reply.get("status") or "no reply")
    output = reply.get("output") or {}
    if "error" in output:
        raise VoiceServiceError(output["error"])
    return base64.b64decode(output["audio_base64"])


def cache_key(text, voice_id):
    return hashlib.sha256(f"{voice_id}\n{text}".encode()).hexdigest()[:20]
