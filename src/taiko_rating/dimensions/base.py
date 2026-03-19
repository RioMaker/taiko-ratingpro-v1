"""基础维度接口定义。

所有维度计算模块必须实现此接口，以支持后续替换和扩展。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..features.note_features import NoteFeature
from ..models.result import WindowMetrics, DimensionScore


class BaseDimension(ABC):
    """维度计算基类。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """维度名称（英文标识）。"""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """维度显示名称（中文）。"""
        ...

    @abstractmethod
    def compute(
        self,
        features: list[NoteFeature],
        window_metrics: list[WindowMetrics],
    ) -> DimensionScore:
        """计算该维度的评分。

        Args:
            features: 音符级特征列表
            window_metrics: 段落级滑窗指标列表

        Returns:
            DimensionScore 包含原始值和标准化分数
        """
        ...

    def _normalize(self, raw: float, floor: float = 0.0,
                   ceiling: float = 10.0, scale: float = 1.0) -> float:
        """通用线性标准化到 0‑10。"""
        val = raw * scale
        return max(floor, min(ceiling, val))
