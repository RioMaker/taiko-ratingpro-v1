# Engine Flow（计算流水线约束）

## 流程顺序（不可随意打乱）

1. `TJAParser` 解析输入谱面
2. `extract_note_features` 提取音符级特征
3. `sliding_window_analysis` 生成窗口指标
4. `get_all_dimensions()` 逐维计算 `DimensionScore`
5. `aggregate_target_difficulty` 计算 pass/fc/acc
6. `generate_hotspots` + `generate_summary` 生成解释
7. 汇总 `BranchResult / ChartResult / SongResult`

## 当前统计字段（`BranchResult.stats`）

- `total_notes`
- `hit_notes`
- `duration_sec`
- `mean_rate`
- `max_rate`
- `median_interval_ms`
- `bpm_range`
- `color_switches`

## Agent 修改规则

- 新增维度时必须同步：
  - `dimensions/` 注册
  - `aggregation/target_difficulty.py` 权重
  - `docs/dimensions.md` 文档
  - 至少 1 条测试用例
- 修改结果结构时必须同步：
  - `models/result.py` 的 `to_dict()`
  - API 输出消费端（Vue 组件）
  - README 输出字段说明
- 不要绕过 `engine.py` 在 API/CLI 中直接拼装评分逻辑。
