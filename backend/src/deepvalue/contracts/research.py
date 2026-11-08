from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo
from typing import Literal
from pydantic import Field, model_validator, field_validator
from .common import Contract


class ResearchRequest(Contract):
    ticker: str = Field(default="GOOGL", pattern=r"^[A-Z][A-Z0-9.-]{0,9}$")
    cik: str = Field(default="1652044", validate_default=True, pattern=r"^[0-9]{1,10}$")
    as_of: date
    industry: Literal["computer_services"] = "computer_services"
    years: int = Field(strict=True, default=3, ge=3, le=5)
    max_rounds: int = Field(strict=True, default=2, ge=1, le=2)
    pe_low: Decimal = Field(default=Decimal("10"), gt=0, le=80)
    pe_base: Decimal = Field(default=Decimal("15"), gt=0, le=80)
    pe_high: Decimal = Field(default=Decimal("20"), gt=0, le=80)
    focus: str = Field(default="广告与云业务、AI资本开支、经营质量与监管风险", max_length=1000)
    model: str = Field(min_length=1, max_length=100)

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value):
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator("cik")
    @classmethod
    def normalize_cik(cls, value):
        return value.zfill(10)

    @model_validator(mode="after")
    def check_scope(self):
        if not date(2010, 1, 1) <= self.as_of <= datetime.now(ZoneInfo("America/New_York")).date():
            raise ValueError("研究截止日须为 2010 年起、且不晚于美国东部当前日期")
        if not self.pe_low < self.pe_base < self.pe_high:
            raise ValueError("市盈率假设必须满足：低情景 < 基准情景 < 高情景")
        return self

