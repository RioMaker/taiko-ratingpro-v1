# Frontend Contract（WebUI 对接约定）

## 技术栈

- Vue 3 + Vite
- 代理：开发模式通过 `vite.config.js` 将 `/api` 转发到 `127.0.0.1:5000`

## 组件职责

- `App.vue`：页面总入口（上传、加载、错误、结果）
- `components/FileUpload.vue`：上传文件 / 文本提交
- `components/RatingResult.vue`：多谱面/分支切换与卡片组织
- `components/TargetDifficulty.vue`：pass/fc/acc 展示
- `components/DimensionChart.vue`：七维评分条
- `components/HotspotList.vue`：难点时间轴与明细

## 后端字段依赖（当前）

- `title`
- `charts[].branches[]`
  - `course`
  - `branch_type`
  - `target_difficulties.pass/fc/acc`
  - `dimensions[]`（`name`, `normalized`）
  - `hotspots[]`（`start`, `end`, `severity`, `primary_dimensions`, `affected_targets`, `explanation`）
  - `summary`
  - `stats`

## Agent 修改规则

- 调整接口字段时，必须同步更新前端消费逻辑。
- 前端只展示，不复制计算逻辑（评分全部以后端为准）。
- 若新增图表或卡片，优先复用当前卡片布局与样式变量。
