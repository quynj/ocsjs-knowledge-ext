import os
from dataclasses import dataclass
from typing import Final, Literal

from dotenv import load_dotenv

load_dotenv()

REQUEST_TIMEOUT_SECONDS: Final[int] = 60
MAX_TITLE_LENGTH: Final[int] = 2000
MAX_OPTIONS_COUNT: Final[int] = 26
ApiType = Literal["chat_completions", "responses"]


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str
    model: str
    api_type: ApiType

    @classmethod
    def from_env(cls) -> "Settings":
        api_type = os.getenv("OPEN_AI_API_TYPE", "chat_completions").strip().lower()
        if api_type not in ("chat_completions", "responses"):
            raise ValueError(
                "OPEN_AI_API_TYPE must be chat_completions or responses"
            )

        return cls(
            api_key=os.getenv("OPEN_AI_API_KEY", "").strip(),
            base_url=(
                os.getenv("OPEN_AI_BASE_URL", "").strip().rstrip("/")
                or "https://api.deepseek.com"
            ),
            model=os.getenv("OPEN_AI_MODEL", "").strip(),
            api_type=api_type,
        )
