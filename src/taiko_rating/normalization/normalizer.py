"""标准化模块。

将原始维度值映射到统一量程，支持规则标准化和后续样本标定。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NormConfig:
    """单维度标准化配置。"""
    floor: float = 0.0
    ceiling: float = 10.0
    # 线性映射：normalized = (raw - raw_min) / (raw_max - raw_min) * (ceiling - floor) + floor
    raw_min: float = 0.0
    raw_max: float = 10.0
    method: str = "linear"  # "linear" | "log" | "quantile"（第一版仅实现 linear）


# 默认标准化参数（可通过外部配置覆盖）
DEFAULT_NORM_CONFIGS: dict[str, NormConfig] = {
    "peak_pressure": NormConfig(raw_min=0.0, raw_max=25.0),
    "sustained_pressure": NormConfig(raw_min=0.0, raw_max=10.0),
    "technique_complexity": NormConfig(raw_min=0.0, raw_max=10.0),
    "rhythm_complexity": NormConfig(raw_min=0.0, raw_max=10.0),
    "reading_complexity": NormConfig(raw_min=0.0, raw_max=15.0),
    "accuracy_pressure": NormConfig(raw_min=0.0, raw_max=10.0),
    "miss_penalty": NormConfig(raw_min=0.0, raw_max=10.0),
}


def normalize_value(
    raw: float,
    config: NormConfig | None = None,
) -> float:
    """将原始值按配置标准化到 [floor, ceiling]。"""
    if config is None:
        config = NormConfig()

    if config.method == "linear":
        spread = config.raw_max - config.raw_min
        if spread <= 0:
            return config.floor
        ratio = (raw - config.raw_min) / spread
        val = ratio * (config.ceiling - config.floor) + config.floor
        return max(config.floor, min(config.ceiling, val))

    # 后续可扩展 log / quantile
    return max(config.floor, min(config.ceiling, raw))


def load_norm_configs(data: dict[str, Any]) -> dict[str, NormConfig]:
    """从字典加载标准化配置（用于外部标定数据）。"""
    configs: dict[str, NormConfig] = {}
    for name, params in data.items():
        configs[name] = NormConfig(**params)
    return configs
