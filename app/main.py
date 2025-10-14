from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body, Query
from typing import Any, Dict, List, Optional, Union
import json
import logging
from .models import AnswerData, QueryRequest, SuccessResponse, ErrorResponse
from .llm import OpenAIChatClient
from .prompt import build_messages
from .parsing import parse_answer
from .config import MAX_TITLE_LENGTH, MAX_OPTIONS_COUNT
from openai import (
    APIError,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    BadRequestError,
    InternalServerError,
)

# 基础日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("ocs-answerer")

app = FastAPI(title="OCS AnswererWrapper Service", version="0.1.0")

# CORS：根据需要收敛来源与头
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.head("/")
async def health():
    return {"status": "ok"}


@app.get("/query", response_model=Union[SuccessResponse, ErrorResponse])
async def query_get(
    title: str = Query(...),
    options: Optional[str] = Query(None, description="题目的选项,可以是JSON数组字符串或以换行分隔的文本"),
    type: Optional[str] = Query(None)
):
    parsed_options: Optional[Union[List[str], List[Dict[str, Any]]]] = None
    if options:
        # 优先尝试 JSON
        try:
            val = json.loads(options)
            if isinstance(val, list):
                parsed_options = val  # 可能是 str[] 或 obj[]
        except Exception:
            # 兼容按换行传输的纯文本选项
            lines = [line.strip() for line in options.splitlines() if line.strip()]
            if lines:
                parsed_options = lines

    req = QueryRequest(
        title=title,
        options=parsed_options,  # type: ignore[arg-type]
        type=type
    )
    return await _process_query(req)


async def _process_query(req: QueryRequest):
    if not req.title:
        return ErrorResponse(code=40002, message="missing title")
    if len(req.title) > MAX_TITLE_LENGTH:
        return ErrorResponse(code=40003, message="title too long")
    if req.options and len(req.options) > MAX_OPTIONS_COUNT:
        return ErrorResponse(code=40003, message="options too long")

    logger.info("request>>> %s",req)

    # 构造 messages
    messages = build_messages(
        title=req.title,
        options=req.options,
        qtype=req.type
    )

    # 调用 LLM
    try:
        client = OpenAIChatClient()
        content = await client.chat(messages)
    except Exception:
        return ErrorResponse(code=50001, message="llm request error")

    # 解析答案
    try:
        parsed = parse_answer(content, req.type, req.options)
    except Exception:
        return ErrorResponse(code=50002, message="parse answer error")

    # 将多选数组转换为 '#'
    if isinstance(parsed, list):
        answer_out: Union[str, List[str]] = "#".join(parsed)
    else:
        answer_out = parsed

    data = AnswerData(answer=answer_out,question=req.title,ai=True)
    logger.info("response>>> %s", data)

    return SuccessResponse(code=0, data=data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
