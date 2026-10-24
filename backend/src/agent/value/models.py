from datetime import date, datetime
from zoneinfo import ZoneInfo
from typing import Literal, Annotated, TypedDict
from pydantic import BaseModel, Field, ConfigDict, model_validator
from langgraph.graph import add_messages


class ResearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    ticker: str = Field(default="CAT", pattern=r"^[A-Z][A-Z0-9.-]{0,9}$")
    cik: str = Field(default="18230", pattern=r"^[0-9]{1,10}$")
    as_of: date
    industry: Literal["machinery"] = "machinery"
    years: int = Field(default=3, ge=3, le=5)
    max_rounds: int = Field(default=2, ge=1, le=2)
    pe_low: float = Field(default=10, gt=0, le=80)
    pe_base: float = Field(default=15, gt=0, le=80)
    pe_high: float = Field(default=20, gt=0, le=80)
    focus: str = Field(default="经营质量、周期风险与资本配置", max_length=1000)
    model: str = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def check_scope(self):
        if not date(2010, 1, 1) <= self.as_of <= datetime.now(ZoneInfo("America/New_York")).date():
            raise ValueError("研究截止日须为 2010 年起、且不晚于美国东部当前日期")
        if not self.pe_low < self.pe_base < self.pe_high:
            raise ValueError("市盈率假设必须满足：低情景 < 基准情景 < 高情景")
        return self


class Citation(BaseModel):
    evidence_id: str
    quote: str = Field(min_length=8, max_length=350)


class Claim(BaseModel):
    topic: Literal["business", "quality", "risk", "policy", "industry"]
    text: str = Field(min_length=1, max_length=800)
    citations: list[Citation] = Field(min_length=1, max_length=3)


class Analysis(BaseModel):
    claims: list[Claim] = Field(max_length=8)
    gaps: list[str] = Field(max_length=6)


def merge_records(left: dict, right: dict) -> dict:
    return {**left, **right}


class ValueState(TypedDict, total=False):
    request: dict
    scope: dict
    messages: Annotated[list, add_messages]
    round: int
    tasks: list[dict]
    completed: Annotated[dict, merge_records]
    evidence: Annotated[dict, merge_records]
    rejected: Annotated[dict, merge_records]
    company: dict
    financials: list[dict]
    financial_issues: list[str]
    collector_errors: Annotated[dict, merge_records]
    analysis: dict
    valuation: dict
    review: dict
    report: str


class TaskState(TypedDict):
    task: dict
    scope: dict
    company: dict
