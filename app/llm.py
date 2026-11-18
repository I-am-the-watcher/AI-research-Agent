"""Thin LLM wrapper. Uses Gemini through its OpenAI-compatible endpoint."""
try:
    from langfuse.openai import OpenAI
except ImportError:  # pragma: no cover
    from openai import OpenAI

from .config import GEMINI_MODEL, GEMINI_API_KEY

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    max_retries=6,
)


def structured(system: str, user: str, schema):
    r = client.beta.chat.completions.parse(
        model=GEMINI_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format=schema,
    )
    return r.choices[0].message.parsed


def text(system: str, user: str) -> str:
    r = client.chat.completions.create(
        model=GEMINI_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return r.choices[0].message.content