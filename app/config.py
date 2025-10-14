from typing import Final

# 服务级别通用配置（不包含任何 LLM 默认配置）
REQUEST_CONNECT_TIMEOUT_SECONDS: Final[int] = 10
REQUEST_READ_TIMEOUT_SECONDS: Final[int] = 60
MAX_TITLE_LENGTH: Final[int] = 2000
MAX_OPTIONS_COUNT: Final[int] = 50
