import json
import logging
from typing import Any

import httpx
from fastapi import Body, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.config import Settings
from app.llm import answer
from app.models import ErrorResponse, OptionObject, QueryRequest, SuccessResponse
from app.parsing import parse_answer
from app.prompt import build_prompt

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("ocs-answerer")

app = FastAPI(title="OCS AnswererWrapper Service", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
@app.head("/")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def _error(code: int, message: str) -> ErrorResponse:
    return ErrorResponse(code=code, message=message)


async def _process_query(request: QueryRequest) -> SuccessResponse | ErrorResponse:
    try:
        settings = Settings.from_env()
    except ValueError as exc:
        logger.warning("Invalid model configuration: %s", exc)
        return _error(50001, str(exc))

    if len(request.title) > settings.max_title_length:
        return _error(40003, "title too long")
    if request.options and len(request.options) > settings.max_options_count:
        return _error(40003, "too many options")
    if request.options:
        labels = [
            (option.label or chr(ord("A") + index)).upper()
            if isinstance(option, OptionObject)
            else chr(ord("A") + index)
            for index, option in enumerate(request.options)
        ]
        if len(labels) != len(set(labels)):
            return _error(40003, "option labels must be unique")

    try:
        system_prompt, user_prompt = build_prompt(
            request.title, request.options, request.type
        )
        raw_answer = await answer(system_prompt, user_prompt, settings)
        parsed_answer = parse_answer(raw_answer, request.type, request.options)
    except ValueError as exc:
        logger.warning("Query could not be processed: %s", exc)
        return _error(50001, str(exc))
    except httpx.HTTPStatusError as exc:
        logger.error("Model API returned HTTP %s", exc.response.status_code)
        return _error(50201, "model API request failed")
    except httpx.HTTPError:
        logger.exception("Unable to connect to model API")
        return _error(50201, "unable to connect to model API")
    return SuccessResponse(
        data={"answer": parsed_answer, "question": request.title, "ai": True}
    )


@app.post("/query")
async def query_post(payload: Any = Body(...)) -> SuccessResponse | ErrorResponse:
    try:
        request = QueryRequest.model_validate(payload)
    except ValidationError as exc:
        return _error(40001, exc.errors()[0]["msg"])
    return await _process_query(request)


@app.get("/query")
async def query_get(
    title: str | None = Query(default=None),
    options: str | None = Query(
        default=None, description="JSON 数组字符串或以换行分隔的选项文本"
    ),
    qtype: str | None = Query(default=None, alias="type"),
) -> SuccessResponse | ErrorResponse:
    if not title or not title.strip():
        return _error(40001, "missing title")
    if not qtype:
        return _error(40002, "missing question type")

    parsed_options: list[Any] | None = None
    if options:
        try:
            value = json.loads(options)
            if isinstance(value, list):
                parsed_options = value
            else:
                return _error(40003, "options must be a JSON array")
        except json.JSONDecodeError:
            parsed_options = [line.strip() for line in options.splitlines() if line.strip()]

    try:
        request = QueryRequest(
            title=title,
            options=parsed_options,
            type=qtype.lower(),
        )
    except ValidationError as exc:
        return _error(40002, exc.errors()[0]["msg"])
    return await _process_query(request)
