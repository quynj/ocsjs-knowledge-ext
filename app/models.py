from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, model_validator


class OptionObject(BaseModel):
    label: Optional[str] = None
    text: str


OptionsType = Union[List[str], List[OptionObject]]


class LLMConfig(BaseModel):
    baseUrl: str = Field(..., description="OpenAI 兼容 API baseUrl，例如 https://api.openai.com")
    apiKey: str = Field(..., description="用户提供的 API Key")
    model: str = Field(..., description="模型名，例如 gpt-4o-mini 或 qwen-plus")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    systemPrompt: Optional[str] = None


class QueryRequest(BaseModel):
    title: str
    options: Optional[OptionsType] = None
    type: Optional[str] = Field(None, description="single | multiple | judge | fill | 任意字符串")

    # LLM 必填
    baseUrl: str
    apiKey: str
    model: str

    # 可选
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    systemPrompt: Optional[str] = None

    @model_validator(mode="after")
    def ensure_llm_required(self) -> "QueryRequest":
        if not self.baseUrl or not self.apiKey or not self.model:
            raise ValueError("missing baseUrl/apiKey/model")
        return self


class AnswerData(BaseModel):
    answer: Union[str, List[str]]
    question: Optional[str] = None
    ai: bool = True
    extra: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    code: int = 0
    data: AnswerData


class ErrorResponse(BaseModel):
    code: int
    message: str
