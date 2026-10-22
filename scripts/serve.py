#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
serve.py
一鍵啟動「國中會考文言文睡眠廣播」本地 Web 播放器伺服器
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"
PORT = 8080

class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def log_message(self, format, *args):
        # 僅印出關鍵資訊，保持終端機乾淨
        if "404" in args[1]:
            print(f"⚠️ [404 Not Found] {args[0]}")

def main():
    os.chdir(WEB_DIR)
    
    # 支援端口佔用自動遞增
    port = PORT
    for attempt in range(10):
        try:
            with socketserver.TCPServer(("", port), QuietHTTPHandler) as httpd:
                url = f"http://localhost:{port}/"
                print("\n" + "=" * 60)
                print("🌙 國中會考文言文睡眠廣播網頁播放器已啟動！")
                print(f"🔗 本地網址：{url}")
                print("💡 按下 Ctrl + C 即可停止伺服器")
                print("=" * 60 + "\n")
                
                # 自動開啟瀏覽器
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
                    
                httpd.serve_forever()
                break
        except OSError:
            port += 1

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 伺服器已安全停止。祝您好夢！")
