import os
import json
from pydantic import BaseModel, Field
from typing import Any, Optional, List
from langchain_core.runnables import RunnableConfig


class ModelConfig(BaseModel):
    """模型配置项"""
    model_id: str = Field(..., description="模型ID")
    display_name: str = Field(..., description="显示名称")
    icon: str = Field(default="Zap", description="图标类型(Zap/Cpu)")
    icon_color: str = Field(default="yellow-400", description="图标颜色")


def load_available_models_from_env() -> List[ModelConfig]:
    """从环境变量加载可用模型列表"""
    from deepvalue.config import parse_models
    return list(parse_models(os.getenv("AVAILABLE_MODELS", "")))


def get_default_model_id() -> str:
    """获取默认模型ID（模型列表的最后一项）"""
    models = load_available_models_from_env()
    if models:
        return models[-1].model_id
    raise ValueError("未配置可用模型")


class Configuration(BaseModel):
    """agent的配置."""

    # 可用模型列表配置（从环境变量加载）
    available_models: List[ModelConfig] = Field(
        default_factory=load_available_models_from_env,
        metadata={"description": "可用的LLM模型列表"},
    )

    query_generator_model: str = Field(
        default_factory=get_default_model_id,
        metadata={
            "description": "用于Agent查询生成的LLM的名称."
        },
    )

    reflection_model: str = Field(
        default_factory=get_default_model_id,
        metadata={
            "description": "用于Agent反思的LLM的名称."
        },
    )

    answer_model: str = Field(
        default_factory=get_default_model_id,
        metadata={
            "description": "用于Agent生成答案的LLM模型名称."
        },
    )

    number_of_initial_queries: int = Field(
        default=2,
        metadata={"description": "要生成的初始搜索查询数量."},
    )

    max_research_loops: int = Field(
        default=2,
        metadata={"description": "要执行的最大research循环次数."},
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """从RunnableConfig创建配置实例."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )

        raw_values: dict[str, Any] = {}
        for name in cls.model_fields.keys():
            # 跳过 available_models，它应该从环境变量直接加载
            if name == "available_models":
                continue
            env_value = os.environ.get(name.upper())
            config_value = configurable.get(name)
            raw_values[name] = env_value if env_value is not None else config_value

        values = {k: v for k, v in raw_values.items() if v is not None}

        return cls(**values)
