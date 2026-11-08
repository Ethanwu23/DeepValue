from datetime import date, datetime
from zoneinfo import ZoneInfo
from typing import Literal, Annotated, TypedDict
from pydantic import BaseModel, Field, ConfigDict, model_validator
from langgraph.graph import add_messages


from deepvalue.contracts.research import ResearchRequest


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
