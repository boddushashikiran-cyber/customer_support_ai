"""
Thin wrapper around the LLM provider so agents don't care whether you're
using OpenAI, Groq (Llama 3), or Gemini's OpenAI-compatible endpoint.

If no API key is set, MOCK_MODE kicks in automatically so the whole system
is runnable and demoable offline (useful while developing / for your demo
video if you don't want to burn API credits).
"""
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("LLM_MODEL", "gpt-4o-mini")
MOCK_MODE = os.getenv("MOCK_MODE", "auto")  # "auto" | "true" | "false"

_client = None


def _use_mock() -> bool:
    if MOCK_MODE == "true":
        return True
    if MOCK_MODE == "false":
        return False
    return not bool(OPENAI_API_KEY)  # auto: mock only if no key configured


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def chat_completion(system_prompt: str, user_prompt: str, history=None) -> str:
    """
    history: list of {"role": "user"|"assistant", "content": str}
    Returns the assistant's reply text.
    """
    if _use_mock():
        return _mock_reply(system_prompt, user_prompt)

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_prompt})

    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.3,
        max_tokens=500,
    )
    return response.choices[0].message.content


def _mock_reply(system_prompt: str, user_prompt: str) -> str:
    """
    Deterministic offline stand-in so the pipeline is fully testable without
    an API key. Replace by setting OPENAI_API_KEY (or MOCK_MODE=false).
    """
    return (
        "[MOCK RESPONSE - set OPENAI_API_KEY in .env for real answers]\n"
        f"Based on the agent instructions and retrieved context, here is a "
        f"draft answer to: \"{user_prompt.strip()[:200]}\""
    )
