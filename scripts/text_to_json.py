#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
text_to_json.py
自動解析文言文 Markdown 檔案，轉化為前端網頁播放器所需的結構化 episodes.json。
"""

import json
import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
WEB_DIR = BASE_DIR / "web"

def parse_markdown_file(file_path, category_name, id_prefix, default_author, default_dynasty):
    content = file_path.read_text(encoding="utf-8")
    
    # 切割每篇 ## 第二篇：【篇名】...
    pattern = r"##\s+第.*?篇：【篇名】(.*?)\n+(?=###\s+【原文】)"
    sections = re.split(r"(##\s+第[一二三四五六七八九十0-9]+篇：【篇名】.*?\n)", content)
    
    episodes = []
    current_title = ""
    
    for i in range(1, len(sections), 2):
        header = sections[i]
        body = sections[i+1] if i+1 < len(sections) else ""
        
        # 提取標題
        title_match = re.search(r"【篇名】(.*?)(?:\n|$)", header)
        full_title = title_match.group(1).strip() if title_match else "未命名篇章"
        
        # 提取短標題
        short_title = full_title
        if "》" in full_title:
            short_title = full_title.split("》")[-1].strip()
        
        # 提取原文
        orig_match = re.search(r"###\s+【原文】\s*\n(.*?)(?=\n###|\Z)", body, re.DOTALL)
        original_text = orig_match.group(1).strip() if orig_match else ""
        
        # 提取關鍵字詞注釋
        notes_match = re.search(r"###\s+【關鍵字詞注釋】\s*\n(.*?)(?=\n###|\Z)", body, re.DOTALL)
        notes_raw = notes_match.group(1).strip() if notes_match else ""
        
        annotations = []
        for line in notes_raw.splitlines():
            line = line.strip()
            # 匹配 1. **詞**：解釋
            m = re.match(r"\d+\.\s*\*\*(.*?)\*\*：\s*(.*)", line)
            if m:
                annotations.append({
                    "term": m.group(1).strip(),
                    "note": m.group(2).strip()
                })
        
        # 提取白話文直譯
        trans_match = re.search(r"###\s+【白話文直譯】\s*\n(.*?)(?=\n###|\Z)", body, re.DOTALL)
        translation = trans_match.group(1).strip() if trans_match else ""
        
        # 提取會考素養提要與核心寓意
        points_match = re.search(r"###\s+【會考素養提要與核心寓意】\s*\n(.*?)(?=\n---|\n##|\Z)", body, re.DOTALL)
        key_points = points_match.group(1).strip() if points_match else ""
        
        idx = len(episodes) + 1
        ep_id = f"{id_prefix}_{idx:02d}"
        
        # 對應的音檔路徑
        audio_filename = f"{ep_id}.mp3"
        
        episodes.append({
            "id": ep_id,
            "category": category_name,
            "title": full_title,
            "short_title": short_title,
            "author": default_author,
            "dynasty": default_dynasty,
            "audio_src": f"audio/{audio_filename}",
            "original_text": original_text,
            "annotations": annotations,
            "translation": translation,
            "key_points": key_points
        })
        
    return episodes

def main():
    all_episodes = []
    
    # 1. 世說新語
    shishuo_file = DATA_DIR / "shishuo_xinyu_classics.md"
    if shishuo_file.exists():
        eps1 = parse_markdown_file(
            shishuo_file,
            category_name="世說新語名士特輯",
            id_prefix="shishuo",
            default_author="劉義慶 主編",
            default_dynasty="南朝宋"
        )
        all_episodes.extend(eps1)
        print(f"成功解析《世說新語》篇章共 {len(eps1)} 篇")
        
    # 2. 諸子寓言
    zhuzi_file = DATA_DIR / "zhuzi_fables.md"
    if zhuzi_file.exists():
        eps2 = parse_markdown_file(
            zhuzi_file,
            category_name="諸子哲理與寓言特輯",
            id_prefix="zhuzi",
            default_author="先秦諸子",
            default_dynasty="先秦"
        )
        all_episodes.extend(eps2)
        print(f"成功解析《諸子哲理與寓言》篇章共 {len(eps2)} 篇")
        
    # 輸出至 data/episodes.json 與 web/episodes.json
    data_out = DATA_DIR / "episodes.json"
    web_out = WEB_DIR / "episodes.json"
    
    payload = {
        "title": "國中會考文言文睡眠廣播",
        "description": "專為國中會考學生睡前聆聽打造的文言文逐篇解讀與白話直譯系統",
        "total_episodes": len(all_episodes),
        "episodes": all_episodes
    }
    
    with open(data_out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        
    with open(web_out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        
    print(f"共生成 {len(all_episodes)} 篇章結構化資料，已寫入 {data_out} 與 {web_out}")

if __name__ == "__main__":
    main()
