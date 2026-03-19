"""一键启动 太鼓达人谱面难度评定系统。

自动检查并构建前端（如需要），然后启动 Web 服务器。
双击运行或执行: python start.py
"""

import os
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEBUI_DIR = ROOT / "webui"
DIST_DIR = WEBUI_DIR / "dist"


def check_flask():
    try:
        import flask  # noqa: F401
        return True
    except ImportError:
        return False


def install_flask():
    print("[1/3] 安装 Flask …")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("      Flask 安装完成 ✓")


def check_npm():
    try:
        subprocess.check_call(["npm", "--version"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def build_frontend():
    if not WEBUI_DIR.exists():
        print("[!] 未找到 webui/ 目录，跳过前端构建")
        return False

    node_modules = WEBUI_DIR / "node_modules"
    if not node_modules.exists():
        print("[2/3] 安装前端依赖 (npm install) …")
        subprocess.check_call(["npm", "install"], cwd=str(WEBUI_DIR))
        print("      前端依赖安装完成 ✓")

    if not DIST_DIR.exists() or not (DIST_DIR / "index.html").exists():
        print("[2/3] 构建前端 (npm run build) …")
        subprocess.check_call(["npm", "run", "build"], cwd=str(WEBUI_DIR))
        print("      前端构建完成 ✓")
    else:
        print("[2/3] 前端已构建 ✓")

    return True


def main():
    host = "127.0.0.1"
    port = 5000
    url = f"http://{host}:{port}"

    print("=" * 50)
    print("  🥁 太鼓达人谱面难度评定系统")
    print("=" * 50)
    print()

    # 1. Flask
    if not check_flask():
        install_flask()
    else:
        print("[1/3] Flask 已安装 ✓")

    # 2. 前端
    if check_npm():
        build_frontend()
    else:
        if DIST_DIR.exists() and (DIST_DIR / "index.html").exists():
            print("[2/3] 前端已构建 ✓ (未检测到 npm，跳过重新构建)")
        else:
            print("[2/3] 未检测到 npm，无法构建前端")
            print("      请先安装 Node.js: https://nodejs.org/")
            print("      或手动执行: cd webui && npm install && npm run build")

    # 3. 启动服务器
    print(f"[3/3] 启动服务器 → {url}")
    print()
    print(f"  浏览器访问: {url}")
    print("  按 Ctrl+C 停止服务器")
    print()

    webbrowser.open(url)

    from taiko_rating.api import run_server
    run_server(host=host, port=port)


if __name__ == "__main__":
    main()
