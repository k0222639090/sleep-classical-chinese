#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_audio_tts.py
=============================================================================
國中會考文言文睡前廣播：高音質語音合成腳本 (基於 Edge-TTS)
特點：
  1. 使用優質台灣國語神經語音 (zh-TW-HsiaoChenNeural / zh-TW-YunJheNeural)
  2. 專為睡前調教：語速微降 -12%，音調溫和，段落停頓沉靜自然
  3. 逐篇完整朗誦：篇名 ➜ 原文吟誦 ➜ 關鍵字詞釋義 ➜ 白話直譯 ➜ 會考要點
  4. 生成 MP3 並同步儲存於 audio/ 與 web/audio/ 目錄
=============================================================================
"""

import asyncio
import json
import os
import re
import sys
from pathlib import Path
import edge_tts

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = BASE_DIR / "audio"
WEB_AUDIO_DIR = BASE_DIR / "web" / "audio"

# 適合睡前聆聽的台灣優質雙聲優
VOICE_FEMALE = "zh-TW-HsiaoChenNeural"  # 溫柔知性，適合白話直譯與引導
VOICE_MALE = "zh-TW-YunJheNeural"      # 沉穩內斂，適合古文原文與考點

def build_spoken_script(ep):
    """
    構造適合睡前閉眼聆聽的客觀、平穩解說語音劇本
    """
    title = ep["title"]
    short_title = ep["short_title"]
    original = ep["original_text"]
    annotations = ep.get("annotations", [])
    translation = ep["translation"]
    key_points = ep.get("key_points", "")
    
    # 清理原文中的標點以利朗誦停頓
    script = []
    
    # 開場前奏
    script.append(f"睡前聽國文。今晚為您解讀的篇章是：{title}。")
    script.append("請放鬆心情，閉上雙眼。我們首先來聆聽原文。")
    
    # 原文
    script.append(f"【原文】：{original}")
    script.append("接下來，為您逐一梳理本篇的核心字詞與會考必備注釋。")
    
    # 注釋 (挑選重要字詞，語速平穩)
    for idx, item in enumerate(annotations, 1):
        term = item["term"]
        note = item["note"]
        # 清除 markdown 粗體
        term = term.replace("*", "")
        note = note.replace("*", "")
        script.append(f"第{idx}個關鍵字詞：{term}。意思是：{note}。")
        
    script.append("接下來，是整篇的白話文直譯。請對照體會文言字句的本意。")
    
    # 白話文
    script.append(f"【白話直譯】：{translation}")
    
    # 會考核心素養
    if key_points:
        clean_points = key_points.replace("*", "").replace("#", "")
        script.append("最後，為您整理本篇的會考素養提要與核心寓意：")
        script.append(f"{clean_points}")
        
    script.append("今晚的這一篇文言文解讀就到這裡。祝您夜夢甜美，安然入睡。")
    
    return "\n\n".join(script)

async def synthesize_episode(ep, voice=VOICE_FEMALE, rate="-10%"):
    ep_id = ep["id"]
    output_filename = f"{ep_id}.mp3"
    audio_path = AUDIO_DIR / output_filename
    web_audio_path = WEB_AUDIO_DIR / output_filename
    
    print(f"\n>> 正在生成 [{ep_id}] {ep['title']}...")
    spoken_text = build_spoken_script(ep)
    
    # 移除特殊標點與符號以防 TTS 引擎解析異常
    spoken_text = re.sub(r"[#*_~`]", "", spoken_text)
    
    communicate = edge_tts.Communicate(
        text=spoken_text,
        voice=voice,
        rate=rate
    )
    
    # 生成至 audio/
    await communicate.save(str(audio_path))
    
    # 同步複製一份至 web/audio/
    import shutil
    shutil.copyfile(audio_path, web_audio_path)
    
    size_kb = audio_path.stat().st_size / 1024
    print(f"   ✅ 完成！音檔已儲存 ({size_kb:.1f} KB)：\n      - {audio_path}\n      - {web_audio_path}")

async def main():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    WEB_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    episodes_file = DATA_DIR / "episodes.json"
    if not episodes_file.exists():
        print("❌ 找不到 episodes.json，請先執行 scripts/text_to_json.py")
        sys.exit(1)
        
    with open(episodes_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    episodes = data.get("episodes", [])
    print(f"📚 共有 {len(episodes)} 個篇章準備進行睡前高音質語音合成。")
    
    # 可以指定參數：例如先合成前 3 首最具代表性的《世說新語》經典，或全部
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    print(f"🎙️ 本次批次合成前 {min(limit, len(episodes))} 篇（語速 -10%，柔和助眠模式）...")
    
    for i in range(min(limit, len(episodes))):
        ep = episodes[i]
        ep_id = ep["id"]
        target_path = AUDIO_DIR / f"{ep_id}.mp3"
        web_target_path = WEB_AUDIO_DIR / f"{ep_id}.mp3"

        if target_path.exists() and target_path.stat().st_size > 10000:
            print(f"⏩ [{ep_id}] 音檔已存在，自動跳過生成並同步至 web/audio/...")
            import shutil
            shutil.copyfile(target_path, web_target_path)
            continue

        try:
            # 統一使用溫暖柔和的台灣女聲 HsiaoChen，保證高速且不塞車
            await synthesize_episode(ep, voice=VOICE_FEMALE)
        except Exception as e:
            print(f"❌ 合成 {ep['id']} 失敗: {e}")
            
    print("\n🎉 音訊生成作業完成！網頁播放器現已具備完整音訊串流。")

if __name__ == "__main__":
    asyncio.run(main())
