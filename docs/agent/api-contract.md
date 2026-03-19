# API Contract（Agent 实施协议）

## 服务入口

- 开发启动：`python -m taiko_rating.api --host 127.0.0.1 --port 5000`
- WSGI 入口：`taiko_rating.api:app`

## 路由定义

### `GET /api/health`

- 返回：`{"status":"ok","version":"0.1.0"}`

### `POST /api/rate`

- 请求：`multipart/form-data`，字段名必须为 `file`
- 处理：尝试编码 `utf-8 / utf-8-sig / shift_jis / gbk`
- 成功：返回 `SongResult.to_dict()`
- 失败：
  - 400：请求参数问题或无法解码
  - 500：评定执行异常

### `POST /api/rate/text`

- 请求：`application/json`
- body：`{"text": "...", "source": "<可选>"}`
- 成功：返回 `SongResult.to_dict()`
- 失败：
  - 400：缺少 `text`
  - 500：评定执行异常

## CORS 与安全边界

- 当前代码层 CORS 允许 `*`。
- 生产环境推荐通过 Nginx 进行 API 白名单控制：
  - `/etc/nginx/snippets/taiko-rating-api-allowlist.conf`
- Agent 不应在无需求前提下扩大 API 暴露范围。

## 兼容性规则

- 新增 API 字段优先“增量添加”，避免删除旧字段。
- 错误响应统一保持 `{"error": "..."}` 格式。
