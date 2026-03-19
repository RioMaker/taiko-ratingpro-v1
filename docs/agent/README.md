# Agent 文档目录

本目录用于存放专门给 AI Agent 使用的项目约束与执行规范。

## 文档清单

- `agent-context.md`：总览上下文（项目定位、关键入口、基础约束）
- `project-map.md`：目录职责与改动落点
- `engine-flow.md`：评分流水线约束与结果结构同步规则
- `api-contract.md`：API 路由、请求/响应、兼容性约束
- `frontend-contract.md`：前端组件职责与字段依赖
- `deploy-ops.md`：Ubuntu 部署形态、白名单策略、运维命令
- `task-checklist.md`：Agent 执行前后检查清单

## 使用建议

1. Agent 接任务后先读 `agent-context.md` 与 `project-map.md`。
2. 涉及具体模块时，按需读取对应 contract 文档。
3. 完成改动后，使用 `task-checklist.md` 做收尾检查。
4. 当项目结构或部署方式变化时，同步更新本目录。
5. 本目录用于“面向 Agent 的约束与流程”，不替代用户文档（README）。
