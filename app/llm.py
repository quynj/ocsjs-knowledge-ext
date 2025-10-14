from typing import Dict, List
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os

load_dotenv()  # 自动加载 .env 到环境变量

class OpenAIChatClient:
    def __init__(self):
        self.base_url = os.getenv("OPEN_AI_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("OPEN_AI_API_KEY", "")
        self.model = os.getenv("OPEN_AI_MODEL", "")
        self.temperature = 0.8
        self.top_p = 1.0

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        async with AsyncOpenAI(api_key=self.api_key, base_url=self.base_url) as client:
            resp = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                top_p=self.top_p,
            )
            return (resp.choices[0].message.content or "").strip()
