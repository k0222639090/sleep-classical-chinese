#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daily_updater.py
=============================================================================
每日雲端自動更新核心引擎 (GitHub Actions / 本地排程通用)
功能：
  1. 檢測已發布之篇章與儲備庫 (upcoming_corpus.json)
  2. 自動選取並解鎖今日最新 1 篇文言文
  3. 自動透過 Edge-TTS 神經語音生成客觀、舒緩、平穩之睡前解讀 MP3
  4. 同步更新 web/episodes.json 與 data/episodes.json
  5. 確保隨時具備未來儲備庫，無需人工介入！
=============================================================================
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
import edge_tts

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
WEB_DIR = BASE_DIR / "web"
DOCS_DIR = BASE_DIR / "docs"
AUDIO_DIR = BASE_DIR / "audio"
WEB_AUDIO_DIR = WEB_DIR / "audio"
DOCS_AUDIO_DIR = DOCS_DIR / "audio"

UPCOMING_FILE = DATA_DIR / "upcoming_corpus.json"
EPISODES_JSON = WEB_DIR / "episodes.json"
DOCS_EPISODES_JSON = DOCS_DIR / "episodes.json"
DATA_EPISODES_JSON = DATA_DIR / "episodes.json"

VOICE_FEMALE = "zh-TW-HsiaoChenNeural"

def build_spoken_script(ep):
    """建構適合睡前聆聽的客觀、平穩解說語音劇本"""
    title = ep["title"]
    original = ep["original_text"]
    annotations = ep.get("annotations", [])
    translation = ep["translation"]
    key_points = ep.get("key_points", "")
    
    script = []
    script.append(f"睡前聽國文。今晚為您解讀的篇章是：{title}。")
    script.append("請放鬆心情，閉上雙眼。我們首先來聆聽原文。")
    script.append(f"【原文】：{original}")
    script.append("接下來，為您逐一梳理本篇的核心字詞與會考必備注釋。")
    
    for idx, item in enumerate(annotations, 1):
        term = item["term"].replace("*", "")
        note = item["note"].replace("*", "")
        script.append(f"第{idx}個關鍵字詞：{term}。意思是：{note}。")
        
    script.append("接下來，是整篇的白話文直譯。請對照體會文言字句的本意。")
    script.append(f"【白話直譯】：{translation}")
    
    if key_points:
        clean_points = key_points.replace("*", "").replace("#", "")
        script.append("最後，為您整理本篇的會考素養提要與核心寓意：")
        script.append(f"{clean_points}")
        
    script.append("今晚的這一篇文言文解讀就到這裡。祝您夜夢甜美，安然入睡。")
    
    text = "\n\n".join(script)
    # 移除特殊符號以利 TTS 順暢讀誦
    text = re.sub(r"[#*_~`★]", "", text)
    return text

async def synthesize_audio(ep, out_path_1, out_path_2):
    """生成 MP3 音檔並存入 audio/ 與 web/audio/"""
    text = build_spoken_script(ep)
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE_FEMALE,
        rate="-10%"
    )
    await communicate.save(str(out_path_1))
    
    import shutil
    shutil.copyfile(out_path_1, out_path_2)
    
    size_kb = out_path_1.stat().st_size / 1024
    print(f"   🎙️ 音檔生成成功 ({size_kb:.1f} KB)：{out_path_1.name}")

async def run_daily_update():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    WEB_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    if not UPCOMING_FILE.exists():
        print(f"❌ 找不到儲備庫檔案：{UPCOMING_FILE}")
        return False
        
    with open(UPCOMING_FILE, "r", encoding="utf-8") as f:
        upcoming_data = json.load(f)
        
    with open(EPISODES_JSON, "r", encoding="utf-8") as f:
        published_data = json.load(f)
        
    published_eps = published_data.get("episodes", [])
    published_ids = {e["id"] for e in published_eps}
    
    upcoming_pool = upcoming_data.get("upcoming_episodes", [])
    
    # 找出尚未發布的第一篇
    target_ep = None
    target_idx = -1
    for i, ep in enumerate(upcoming_pool):
        if ep["id"] not in published_ids:
            target_ep = ep
            target_idx = i
            break
            
    if not target_ep:
        print("🎉 儲備庫所有篇章皆已發布完成！請在 upcoming_corpus.json 中補充新篇章。")
        return False
        
    print(f"\n=======================================================")
    print(f"🌙 【今日文言文自動更新程序啟動】")
    print(f"📅 日期：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📖 今日即將上新篇章：[{target_ep['id']}] {target_ep['title']}")
    print(f"=======================================================\n")
    
    ep_id = target_ep["id"]
    audio_filename = f"{ep_id}.mp3"
    target_path_1 = AUDIO_DIR / audio_filename
    target_path_2 = WEB_AUDIO_DIR / audio_filename
    target_path_3 = DOCS_AUDIO_DIR / audio_filename
    
    # 設定音檔網址
    target_ep["audio_src"] = f"audio/{audio_filename}"
    target_ep["publish_date"] = datetime.now().strftime("%Y-%m-%d")
    
    # 執行音訊合成
    await synthesize_audio(target_ep, target_path_1, target_path_2)
    import shutil
    shutil.copyfile(target_path_1, target_path_3)
    
    # 加入已發布清單
    published_eps.append(target_ep)
    published_data["total_episodes"] = len(published_eps)
    published_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 寫入 web/episodes.json, docs/episodes.json 與 data/episodes.json
    with open(EPISODES_JSON, "w", encoding="utf-8") as f:
        json.dump(published_data, f, ensure_ascii=False, indent=2)
        
    with open(DOCS_EPISODES_JSON, "w", encoding="utf-8") as f:
        json.dump(published_data, f, ensure_ascii=False, indent=2)
        
    with open(DATA_EPISODES_JSON, "w", encoding="utf-8") as f:
        json.dump(published_data, f, ensure_ascii=False, indent=2)
        
    remaining = len(upcoming_pool) - (target_idx + 1)
    print(f"\n✅ 成功將「{target_ep['short_title']}」發布至網站！")
    print(f"📊 目前網站總篇數：{len(published_eps)} 篇")
    print(f"📦 雲端儲備庫尚存：{remaining} 篇未來篇章待發布。")
    return True

if __name__ == "__main__":
    asyncio.run(run_daily_update())
