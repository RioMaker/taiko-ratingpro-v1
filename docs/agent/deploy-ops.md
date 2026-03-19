# Deploy Ops（Ubuntu 部署与运维）

## 标准部署形态

- 入口层：Nginx（80端口，静态资源 + API 反向代理）
- 应用层：Gunicorn 托管 Flask `taiko_rating.api:app`
- 进程托管：systemd（`taiko-rating.service`）

## 模板来源

- `deploy/ubuntu/gunicorn.conf.py`
- `deploy/ubuntu/taiko-rating.service`
- `deploy/ubuntu/nginx-taiko-rating.conf`
- `deploy/ubuntu/nginx-api-allowlist.conf`
- `deploy/ubuntu/deploy.sh`

## API 白名单策略

- Nginx 默认 `location /api/ { return 403; }`
- 允许接口在 `/etc/nginx/snippets/taiko-rating-api-allowlist.conf` 中显式声明
- 默认建议仅开放：`/api/health`
- 按需开放：`/api/rate`、`/api/rate/text`

## 常用运维命令

```bash
systemctl status taiko-rating
journalctl -u taiko-rating -f
nginx -t
systemctl reload nginx
```

## Agent 修改规则

- 改动 `deploy/ubuntu/` 后必须同步 README 部署章节。
- 任何“扩大 API 暴露面”的改动需要在文档明确写出风险与回滚方式。
- 不在部署模板中硬编码敏感信息（令牌、密码、私钥）。
