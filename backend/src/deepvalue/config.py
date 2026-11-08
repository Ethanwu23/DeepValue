import hashlib
import json
from collections.abc import Mapping
from pydantic import SecretStr
from deepvalue.contracts.common import CapabilityError, Contract


class ModelConfig(Contract):
    model_id: str
    display_name: str
    icon: str = "Zap"
    icon_color: str = "yellow-400"


def parse_models(raw: str) -> tuple[ModelConfig, ...]:
    try:
        values = json.loads(raw)
        if not isinstance(values, list) or not values:
            raise ValueError()
        models = tuple(ModelConfig.model_validate(v) for v in values)
        if any(not m.model_id.strip() for m in models) or len({m.model_id for m in models}) != len(models):
            raise ValueError()
        return models
    except (ValueError, TypeError):
        raise CapabilityError("CONFIG_ERROR", "config", "AVAILABLE_MODELS 必须为非空且编号唯一的模型列表") from None


class Settings(Contract):
    app_token: SecretStr
    llm_base_url: str
    mcp_app_id: SecretStr
    fred_api_key: SecretStr
    sec_user_agent: SecretStr
    models: tuple[ModelConfig, ...]

    @classmethod
    def load(cls, env: Mapping[str, str]):
        names = ("APP_TOKEN", "LLM_BASE_URL", "MCP_APP_ID", "FRED_API_KEY", "SEC_USER_AGENT", "AVAILABLE_MODELS")
        missing = [k for k in names if not env.get(k, "").strip()]
        if missing:
            raise CapabilityError("CONFIG_ERROR", "config", "缺少配置项：" + ", ".join(missing))
        from urllib.parse import urlsplit
        url = urlsplit(env["LLM_BASE_URL"])
        if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query:
            raise CapabilityError("CONFIG_ERROR", "config", "LLM_BASE_URL 格式不符合要求")
        return cls(app_token=SecretStr(env["APP_TOKEN"]), llm_base_url=env["LLM_BASE_URL"],
                   mcp_app_id=SecretStr(env["MCP_APP_ID"]), fred_api_key=SecretStr(env["FRED_API_KEY"]),
                   sec_user_agent=SecretStr(env["SEC_USER_AGENT"]), models=parse_models(env["AVAILABLE_MODELS"]))

    def public_snapshot(self):
        # 不导出密钥、密钥哈希或包含联系方式的 User-Agent。
        value = {"models": [m.model_dump() for m in self.models]}
        value["version"] = hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
        return value
