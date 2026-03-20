# Deploy Ops（部署与运维）

## 一、Docker 部署形态

- 构建文件：`Dockerfile`（多阶段：node 构建前端 + python 运行时）
- 编排文件：`docker-compose.yml`
- 排除文件：`.dockerignore`
- 运行时使用 Gunicorn 托管 Flask，绑定 `0.0.0.0:5000`
- 前端静态文件由 Flask 直接提供（不经过 Nginx）
- `GUNICORN_CMD_ARGS` 环境变量可覆盖 worker 数量、超时等参数

### 常用 Docker 命令

```bash
docker compose up -d          # 构建并启动
docker compose logs -f        # 查看日志
docker compose down           # 停止
docker compose up -d --build  # 重新构建后启动
```

### 路径约束

`api.py` 中 `WEBUI_DIST` 通过 `Path(__file__).parent.parent.parent / "webui" / "dist"` 解析。
Dockerfile 使用 `PYTHONPATH=/app/src` 使 `__file__` 指向 `/app/src/taiko_rating/api.py`，
从而正确解析到 `/app/webui/dist`。修改目录结构时必须确认此路径链不断裂。

## 二、Ubuntu 部署形态

- 入口层：Nginx（80端口，静态资源 + API 反向代理）
- 应用层：Gunicorn 托管 Flask `taiko_rating.api:app`
- 进程托管：systemd（`taiko-rating.service`）

### 模板来源

- `deploy/ubuntu/gunicorn.conf.py`
- `deploy/ubuntu/taiko-rating.service`
- `deploy/ubuntu/nginx-taiko-rating.conf`
- `deploy/ubuntu/nginx-api-allowlist.conf`
- `deploy/ubuntu/deploy.sh`

### API 白名单策略

- Nginx 默认 `location /api/ { return 403; }`
- 允许接口在 `/etc/nginx/snippets/taiko-rating-api-allowlist.conf` 中显式声明
- 默认建议仅开放：`/api/health`
- 按需开放：`/api/rate`、`/api/rate/text`

### 常用运维命令

```bash
systemctl status taiko-rating
journalctl -u taiko-rating -f
nginx -t
systemctl reload nginx
```

## Agent 修改规则

- 改动 `deploy/ubuntu/` 后必须同步 README 部署章节。
- 改动 `Dockerfile` / `docker-compose.yml` 后必须同步 README Docker 部署章节。
- 任何"扩大 API 暴露面"的改动需要在文档明确写出风险与回滚方式。
- 不在部署模板或 Docker 配置中硬编码敏感信息（令牌、密码、私钥）。
