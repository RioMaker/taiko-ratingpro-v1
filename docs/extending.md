# 如何扩展新维度

## 步骤

### 1. 创建维度类

在 `src/taiko_rating/dimensions/` 下创建新文件，例如 `my_dimension.py`：

```python
from .base import BaseDimension
from ..features.note_features import NoteFeature
from ..models.result import WindowMetrics, DimensionScore


class MyDimension(BaseDimension):
    name = "my_dimension"
    display_name = "我的新维度"

    def compute(
        self,
        features: list[NoteFeature],
        window_metrics: list[WindowMetrics],
    ) -> DimensionScore:
        if not features:
            return DimensionScore(name=self.name, raw_value=0.0, normalized=0.0)

        # 计算逻辑
        raw = ...
        normalized = self._normalize(raw)

        return DimensionScore(
            name=self.name,
            raw_value=raw,
            normalized=normalized,
            details={"my_detail": ...},
        )
```

### 2. 注册维度

在 `src/taiko_rating/dimensions/__init__.py` 中：

```python
from .my_dimension import MyDimension

def get_all_dimensions():
    return [
        ...,
        MyDimension(),
    ]
```

### 3. 配置聚合权重

在 `aggregation/target_difficulty.py` 的 `DEFAULT_PROFILES` 中为三种目标难度添加新维度的权重：

```python
TargetDifficulty.PASS: AggregationProfile(
    weights={
        ...,
        "my_dimension": 0.10,
    },
),
```

### 4. 添加测试

在 `tests/test_dimensions.py` 中添加新维度的测试用例。

### 5. 更新文档

在 `docs/dimensions.md` 中添加新维度的说明。

## 替换现有维度算法

如果需要替换某个维度的计算逻辑（例如将规则版手法复杂度替换为 DP 模型），只需：

1. 创建新的类继承 `BaseDimension`，保持相同的 `name`
2. 在 `get_all_dimensions()` 中替换旧实例
3. 保持 `compute()` 接口一致即可

## 添加新的音符特征

如需为新维度添加额外的音符级特征：

1. 在 `NoteFeature` 数据类中添加新字段（设默认值以保持兼容）
2. 在 `extract_note_features()` 中计算新字段
3. 如需要向量化，在 `features_to_arrays()` 中添加对应数组

## 添加新的滑窗指标

在 `WindowMetrics` 中添加新字段，在 `_compute_window_metrics()` 中计算。
