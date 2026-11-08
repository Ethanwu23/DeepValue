from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    """公共契约拒绝未知字段，并禁止就地修改。"""
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class ErrorInfo(Contract):
    code: str
    capability: str
    retryable: bool = False
    safe_detail: str
    task_id: str | None = None


class CapabilityError(RuntimeError):
    """异常只携带可公开的诊断信息。"""
    def __init__(self, code: str, capability: str, detail: str):
        self.info = ErrorInfo(code=code, capability=capability, safe_detail=detail)
        super().__init__(detail)


class Citation(Contract):
    evidence_id: str
    locator: str
    quote: str = Field(min_length=8, max_length=350)


class Claim(Contract):
    claim_id: str
    question_id: str
    kind: Literal["fact", "derived", "inference"]
    text: str
    citations: tuple[Citation, ...] = Field(min_length=1)
    assumptions: tuple[str, ...] = ()


class Reflection(Contract):
    claim_id: str
    action: Literal["keep", "revise", "withdraw"]
    reason: str
    counterevidence_ids: tuple[str, ...] = ()


class RoleResult(Contract):
    role: Literal["bull", "bear", "judge"]
    evidence_version: str
    initial_claims: tuple[Claim, ...] = Field(max_length=8)
    reflection: tuple[Reflection, ...]
    revised_claims: tuple[Claim, ...] = Field(max_length=8)

    @model_validator(mode="after")
    def check_lineage(self):
        initial = {c.claim_id for c in self.initial_claims}
        final = {c.claim_id for c in self.revised_claims}
        reviewed = [r.claim_id for r in self.reflection]
        if len(initial) != len(self.initial_claims) or len(final) != len(self.revised_claims):
            raise ValueError("判断编号重复")
        if len(set(reviewed)) != len(reviewed) or set(reviewed) != initial:
            raise ValueError("反思必须逐一覆盖初判")
        withdrawn = {r.claim_id for r in self.reflection if r.action == "withdraw"}
        if not final <= initial or final & withdrawn:
            raise ValueError("修订结果不得包含新增或撤回的编号")
        return self
