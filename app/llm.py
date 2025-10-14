from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI


class OpenAICompatibleClient:
    def __init__(self, base_url: str, api_key: str, model: str, *, temperature: Optional[float] = None, top_p: Optional[float] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.top_p = top_p

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        async with AsyncOpenAI(api_key=self.api_key, base_url=self.base_url) as client:
            resp = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                top_p=self.top_p,
            )
            return (resp.choices[0].message.content or "").strip()
