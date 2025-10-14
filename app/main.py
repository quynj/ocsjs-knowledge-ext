from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body, Query
from typing import Any, Dict, List, Optional, Union
import json

from .models import QueryRequest, SuccessResponse, ErrorResponse, OptionObject
from .llm import OpenAICompatibleClient
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

app = FastAPI(title="OCS AnswererWrapper Service", version="0.1.0")

# CORS：根据需要收敛来源与头
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


def _normalize_options(options: Optional[Union[List[str], List[Dict[str, Any]], List[OptionObject]]]) -> Optional[List[str]]:
    if options is None:
        return None
    normalized: List[str] = []
    for item in options:  # type: ignore[assignment]
        if isinstance(item, str):
            normalized.append(item)
        elif isinstance(item, OptionObject):
            normalized.append(item.text)
        elif isinstance(item, dict):
            text = item.get("text")
            if isinstance(text, str):
                normalized.append(text)
    return normalized[:MAX_OPTIONS_COUNT]


async def _process_query(req: QueryRequest):
    # 基础限制与校验
    if not req.baseUrl or not req.apiKey or not req.model:
        return ErrorResponse(code=40001, message="missing baseUrl/apiKey/model")
    if not req.title:
        return ErrorResponse(code=40002, message="missing title")
    if len(req.title) > MAX_TITLE_LENGTH:
        return ErrorResponse(code=40003, message="title too long")

    options_list = _normalize_options(req.options)

    # 构造 messages
    messages = build_messages(
        title=req.title,
        options=options_list,
        qtype=req.type,
        system_prompt=req.systemPrompt,
    )

    # 调用 LLM
    try:
        client = OpenAICompatibleClient(
            base_url=req.baseUrl,
            api_key=req.apiKey,
            model=req.model,
            temperature=req.temperature,
            top_p=req.top_p,
        )
        content = await client.chat(messages)
    except AuthenticationError:
        return ErrorResponse(code=40101, message="llm auth error")
    except PermissionDeniedError:
        return ErrorResponse(code=40301, message="llm permission denied")
    except RateLimitError:
        return ErrorResponse(code=42901, message="llm rate limited")
    except APITimeoutError:
        return ErrorResponse(code=50011, message="llm timeout")
    except APIConnectionError:
        return ErrorResponse(code=50012, message="llm connection error")
    except BadRequestError:
        return ErrorResponse(code=40010, message="llm bad request")
    except InternalServerError:
        return ErrorResponse(code=50201, message="llm upstream error")
    except APIError:
        return ErrorResponse(code=50001, message="llm request error")
    except Exception:
        return ErrorResponse(code=50001, message="llm request error")

    # 解析答案
    try:
        parsed = parse_answer(content, req.type, options_list)
    except Exception:
        return ErrorResponse(code=50002, message="parse answer error")

    return SuccessResponse(code=0, data={"answer": parsed, "question": req.title, "ai": True})


@app.post("/query", response_model=Union[SuccessResponse, ErrorResponse])
async def query_post(payload: QueryRequest = Body(...)):
    return await _process_query(payload)


@app.get("/query", response_model=Union[SuccessResponse, ErrorResponse])
async def query_get(
    title: str = Query(...),
    options: Optional[str] = Query(None, description="JSON 数组字符串，如 [\"A\",\"B\"] 或 [{text:\"...\"}]"),
    type: Optional[str] = Query(None),
    baseUrl: str = Query(...),
    apiKey: str = Query(...),
    model: str = Query(...),
    temperature: Optional[float] = Query(None, ge=0.0, le=2.0),
    top_p: Optional[float] = Query(None, ge=0.0, le=1.0),
    systemPrompt: Optional[str] = Query(None)
):
    parsed_options: Optional[Union[List[str], List[Dict[str, Any]]]] = None
    if options:
        try:
            val = json.loads(options)
            if isinstance(val, list):
                parsed_options = val  # 可能是 str[] 或 obj[]
        except Exception:
            parsed_options = None

    req = QueryRequest(
        title=title,
        options=parsed_options,  # type: ignore[arg-type]
        type=type,
        baseUrl=baseUrl,
        apiKey=apiKey,
        model=model,
        temperature=temperature,
        top_p=top_p,
        systemPrompt=systemPrompt
    )
    return await _process_query(req)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
