import json
from pydantic import BaseModel, ValidationError
from deepvalue.contracts.common import CapabilityError


def parse_structured(text: str, schema: type[BaseModel]):
    """结构解析失败不再次请求模型，也不退回自由文本。"""
    try:
        return schema.model_validate_json(text)
    except (ValidationError, ValueError, TypeError):
        raise CapabilityError("MODEL_OUTPUT_INVALID", "model", "模型输出未通过结构校验") from None


def invoke_structured(send, prompt, schema, budget):
    """send由供应商适配器注入；禁止其自行重试，网络准入先计账。"""
    budget.reserve(model=True)
    try:
        text = send(prompt, timeout=min(60, budget.remaining()))
    except Exception:
        raise CapabilityError("SOURCE_UNAVAILABLE", "model", "模型请求失败") from None
    return parse_structured(text, schema)
