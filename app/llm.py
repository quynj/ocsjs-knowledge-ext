from typing import Any

import httpx

from app.config import REQUEST_TIMEOUT_SECONDS, Settings


def _response_text(payload: dict[str, Any], api_type: str) -> str:
    if api_type == "chat_completions":
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Chat Completions response has no choices")
        if not isinstance(choices[0], dict):
            raise ValueError("Chat Completions response has an invalid choice")
        message = choices[0].get("message", {})
        if not isinstance(message, dict):
            raise ValueError("Chat Completions response has an invalid message")
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            return "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            ).strip()
        raise ValueError("Chat Completions response has no text content")

    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    parts: list[str] = []
    output = payload.get("output", [])
    if not isinstance(output, list):
        raise ValueError("Responses API response has an invalid output")
    for item in output:
        if not isinstance(item, dict):
            continue
        contents = item.get("content", [])
        if not isinstance(contents, list):
            continue
        for content in contents:
            if (
                isinstance(content, dict)
                and content.get("type") in ("output_text", "text")
                and isinstance(content.get("text"), str)
            ):
                parts.append(content["text"])
    if parts:
        return "".join(parts).strip()
    raise ValueError("Responses API response has no text content")


async def answer(system_prompt: str, user_prompt: str, settings: Settings) -> str:
    if not settings.api_key or not settings.model:
        raise ValueError("OPEN_AI_API_KEY and OPEN_AI_MODEL must be configured")

    if settings.api_type == "chat_completions":
        endpoint = f"{settings.base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": settings.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
    else:
        endpoint = f"{settings.base_url}/responses"
        payload = {
            "model": settings.model,
            "instructions": system_prompt,
            "input": user_prompt,
        }

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.post(
            endpoint,
            headers={"Authorization": f"Bearer {settings.api_key}"},
            json=payload,
        )
        response.raise_for_status()
        result = response.json()

    if not isinstance(result, dict):
        raise ValueError("The model API returned an invalid response")
    return _response_text(result, settings.api_type)
