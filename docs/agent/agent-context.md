# Agent Context（项目上下文）

## 1. 项目定位

Taiko Rating Pro 是太鼓达人谱面多维难度评定系统，核心算法在 Python 中实现，前端为 Vue，后端为 Flask API。

## 2. 关键入口

- 后端主流程：`src/taiko_rating/engine.py`
- API 入口：`src/taiko_rating/api.py`
- CLI 入口：`src/taiko_rating/cli.py`
- 一键启动：`start.py`
- 前端入口：`webui/src/App.vue`

## 3. 代码与修改约束

- 优先小步、最小修改，避免无关重构。
- 修改行为要与现有目录结构和命名保持一致。
- 涉及部署配置时，优先复用 `deploy/ubuntu/` 下模板。
- 新增能力需同步 README 和相关 docs。

详见：`project-map.md`、`engine-flow.md`、`task-checklist.md`

## 4. 测试与验证

- Python 逻辑优先运行：`pytest tests/ -v`
- 前端改动后可运行：`cd webui && npm run build`
- 部署改动需检查 Nginx/Gunicorn 模板一致性。

详见：`task-checklist.md`

## 5. 生产部署约定（Ubuntu）

- 网站入口由 Nginx 提供静态资源。
- 后端由 Gunicorn 托管 Flask。
- API 通过 Nginx 白名单文件按接口开放：
  - `/etc/nginx/snippets/taiko-rating-api-allowlist.conf`

详见：`deploy-ops.md`

## 6. 输出风格约定

- 结论先行，步骤清晰。
- 涉及文件时给出明确路径。
- 若存在风险或前置条件，明确提示。

接口与前端字段约束详见：`api-contract.md`、`frontend-contract.md`

## 7. 当前阶段策略（MVP）

- 当前阶段仅实现“项目必要功能”，不主动扩展可选特性。
- 未被明确提出的增强项（UI 美化、额外接口、复杂重构）默认延期。
- 需求不明确时，按最小可用实现落地，并在说明中列出可后续扩展点。
