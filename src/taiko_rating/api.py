"""Flask API — Web 接口层。

提供 REST API 供前端调用，支持上传 TJA 文件或提交 TJA 文本进行评定。

启动方式:
  python -m taiko_rating.api [--port 5000] [--host 127.0.0.1]
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from flask.typing import ResponseReturnValue

from .engine import RatingEngine

# 前端静态文件目录（构建后的 Vue 产物）
WEBUI_DIST = Path(__file__).resolve().parent.parent.parent / "webui" / "dist"

app = Flask(__name__, static_folder=str(WEBUI_DIST), static_url_path="")
engine = RatingEngine()


# ---- CORS 中间件 ----

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


# ---- API 路由 ----

@app.route("/api/health", methods=["GET"])
def health() -> ResponseReturnValue:
    return jsonify({"status": "ok", "version": "0.1.0"})


@app.route("/api/rate", methods=["POST"])
def rate_file() -> ResponseReturnValue:
    """上传 TJA 文件进行评定。"""
    if "file" not in request.files:
        return jsonify({"error": "未提供文件，请使用 multipart/form-data 上传 file 字段"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "文件名为空"}), 400

    try:
        content = file.read()
        # 尝试多种编码
        text = None
        for enc in ("utf-8", "utf-8-sig", "shift_jis", "gbk"):
            try:
                text = content.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if text is None:
            return jsonify({"error": "无法解码文件，请确认编码格式"}), 400

        song = engine._parser.parse_text(text, source=file.filename)
        result = engine.rate_song(song)
        return jsonify(result.to_dict())

    except Exception as e:
        return jsonify({"error": f"评定失败: {str(e)}"}), 500


@app.route("/api/rate/text", methods=["POST"])
def rate_text() -> ResponseReturnValue:
    """提交 TJA 文本进行评定。"""
    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "请提供 JSON body: {\"text\": \"TJA内容\"}"}), 400

    text = data["text"]
    source = data.get("source", "<paste>")

    try:
        song = engine._parser.parse_text(text, source=source)
        result = engine.rate_song(song)
        return jsonify(result.to_dict())
    except Exception as e:
        return jsonify({"error": f"评定失败: {str(e)}"}), 500


# ---- 前端静态文件服务 ----

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path: str) -> ResponseReturnValue:
    """提供 Vue 构建产物或 fallback 到 index.html（SPA 路由支持）。"""
    if WEBUI_DIST.exists():
        file_path = WEBUI_DIST / path
        if file_path.is_file():
            return send_from_directory(str(WEBUI_DIST), path)
        index = WEBUI_DIST / "index.html"
        if index.exists():
            return send_from_directory(str(WEBUI_DIST), "index.html")
    return jsonify({
        "message": "前端未构建，请先执行: cd webui && npm install && npm run build",
        "api_docs": {
            "POST /api/rate": "上传 TJA 文件",
            "POST /api/rate/text": "提交 TJA 文本",
            "GET /api/health": "健康检查",
        }
    })


# ---- 入口 ----

def run_server(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Taiko Rating Pro API Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    run_server(args.host, args.port, args.debug)
