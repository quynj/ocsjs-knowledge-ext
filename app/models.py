from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, model_validator


class OptionObject(BaseModel):
    label: Optional[str] = None
    text: str


OptionsType = Union[List[str], List[OptionObject]]


class QueryRequest(BaseModel):
    title: str
    # 允许字符串（\n 分隔）或数组/对象数组
    options: Optional[Union[str, OptionsType]] = None
    type: Optional[str] = Field(None, description="single | multiple | judgement | fill | 任意字符串")

    @model_validator(mode="after")
    def valid_title(self) -> "QueryRequest":
        if not self.title:
            raise ValueError("missing title")
        return self


class AnswerData(BaseModel):
    answer: Union[str, List[str]]
    question: Optional[str] = None
    ai: bool = True


class SuccessResponse(BaseModel):
    code: int = 0
    data: AnswerData


class ErrorResponse(BaseModel):
    code: int
    message: str
