import os
from dataclasses import dataclass
from typing import Final, Literal

from dotenv import load_dotenv

load_dotenv()

REQUEST_TIMEOUT_SECONDS: Final[int] = 60
MAX_TITLE_LENGTH: Final[int] = 2000
MAX_OPTIONS_COUNT: Final[int] = 26
MAX_SUPPORTED_OPTIONS_COUNT: Final[int] = 26
ApiType = Literal["chat_completions", "responses"]


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str
    model: str
    api_type: ApiType
    request_timeout_seconds: int = REQUEST_TIMEOUT_SECONDS
    temperature: float | None = None
    max_title_length: int = MAX_TITLE_LENGTH
    max_options_count: int = MAX_OPTIONS_COUNT

    @classmethod
    def from_env(cls) -> "Settings":
        api_type = os.getenv("OPEN_AI_API_TYPE", "chat_completions").strip().lower()
        if api_type not in ("chat_completions", "responses"):
            raise ValueError(
                "OPEN_AI_API_TYPE must be chat_completions or responses"
            )

        try:
            request_timeout_seconds = int(
                os.getenv(
                    "OPEN_AI_REQUEST_TIMEOUT_SECONDS",
                    str(REQUEST_TIMEOUT_SECONDS),
                )
            )
            max_title_length = int(
                os.getenv("MAX_TITLE_LENGTH", str(MAX_TITLE_LENGTH))
            )
            max_options_count = int(
                os.getenv("MAX_OPTIONS_COUNT", str(MAX_OPTIONS_COUNT))
            )
        except ValueError as exc:
            raise ValueError(
                "OPEN_AI_REQUEST_TIMEOUT_SECONDS, MAX_TITLE_LENGTH, and "
                "MAX_OPTIONS_COUNT must be integers"
            ) from exc

        if request_timeout_seconds <= 0:
            raise ValueError("OPEN_AI_REQUEST_TIMEOUT_SECONDS must be greater than 0")
        if max_title_length <= 0:
            raise ValueError("MAX_TITLE_LENGTH must be greater than 0")
        if not 1 <= max_options_count <= MAX_SUPPORTED_OPTIONS_COUNT:
            raise ValueError(
                f"MAX_OPTIONS_COUNT must be between 1 and {MAX_SUPPORTED_OPTIONS_COUNT}"
            )

        raw_temperature = os.getenv("OPEN_AI_TEMPERATURE", "").strip()
        temperature = None
        if raw_temperature:
            try:
                temperature = float(raw_temperature)
            except ValueError as exc:
                raise ValueError("OPEN_AI_TEMPERATURE must be a number between 0 and 2") from exc
            if not 0 <= temperature <= 2:
                raise ValueError("OPEN_AI_TEMPERATURE must be between 0 and 2")

        return cls(
            api_key=os.getenv("OPEN_AI_API_KEY", "").strip(),
            base_url=(
                os.getenv("OPEN_AI_BASE_URL", "").strip().rstrip("/")
                or "https://api.deepseek.com"
            ),
            model=os.getenv("OPEN_AI_MODEL", "").strip(),
            api_type=api_type,
            request_timeout_seconds=request_timeout_seconds,
            temperature=temperature,
            max_title_length=max_title_length,
            max_options_count=max_options_count,
        )
