# Project Map（Agent 快速定位）

## 目录职责

- `src/taiko_rating/models/`：核心数据结构（谱面模型、结果模型、枚举）
- `src/taiko_rating/parsers/`：TJA 解析
- `src/taiko_rating/features/`：音符级特征提取
- `src/taiko_rating/analysis/`：滑窗分析（段落指标）
- `src/taiko_rating/dimensions/`：七维难度计算
- `src/taiko_rating/aggregation/`：三类目标难度聚合
- `src/taiko_rating/explanation/`：难点与总结生成
- `src/taiko_rating/engine.py`：总编排入口
- `src/taiko_rating/cli.py`：命令行入口
- `src/taiko_rating/api.py`：Flask API + 静态文件服务
- `webui/`：Vue3 前端
- `deploy/ubuntu/`：Gunicorn + systemd + Nginx 部署模板

## 关键入口

- 单文件评定：`RatingEngine.rate_file(path)`
- 歌曲评定：`RatingEngine.rate_song(song)`
- 分支评定：`RatingEngine.rate_branch(branch, chart)`
- API 启动：`python -m taiko_rating.api --port 5000`
- 一键启动：`python start.py`

## 变更落点指引

- 算法逻辑变化：`src/taiko_rating/dimensions/` + `aggregation/`
- 返回字段变化：`models/result.py` + `engine.py` + `api.py` + `webui/`
- Web 交互变化：`webui/src/components/`
- 生产部署变化：`deploy/ubuntu/` + `README.md`
