from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints, field_validator

QuestionType = Literal[
    "single",
    "multiple",
    "judge",
    "judgement",
    "judgment",
    "truefalse",
    "tf",
]
NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class OptionObject(BaseModel):
    label: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1, pattern="^[A-Za-z]$")
    ] | None = None
    text: NonEmptyString


Option = str | OptionObject


class QueryRequest(BaseModel):
    title: NonEmptyString
    options: list[Option] | None = None
    type: QuestionType

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, value: str) -> str:
        return value.lower() if isinstance(value, str) else value


class AnswerData(BaseModel):
    answer: str
    question: str
    ai: bool = True


class SuccessResponse(BaseModel):
    code: Literal[0] = 0
    data: AnswerData


class ErrorResponse(BaseModel):
    code: int
    message: str
