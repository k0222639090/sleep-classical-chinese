#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
notebooklm_automator.py
=============================================================================
Google NotebookLM 自動化串接腳本（Playwright 瀏覽器自動化）
功能：
  1. 支援 Google 帳號持久化 Session 儲存（免重複登入，抗機器人驗證）
  2. 自動登入並導航至 NotebookLM
  3. 自動建立全新筆記本 (New Notebook)
  4. 自動上傳/注入結構化文言文 Markdown 檔案
  5. 自動設定自訂提示詞 (Custom Prompt) 並觸發 Audio Overview (語音總覽) 生成
  6. 輪詢等候生成完成，自動下載 MP3 音訊至專案 audio/ 與 web/audio/ 目錄
=============================================================================
"""

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# 專案目錄定義
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = BASE_DIR / "audio"
WEB_AUDIO_DIR = BASE_DIR / "web" / "audio"
SESSION_DIR = BASE_DIR / ".notebooklm_session"

NOTEBOOKLM_URL = "https://notebooklm.google.com/"

DEFAULT_PROMPT = (
    "請兩位主持人逐篇詳細介紹文件中的每一個文言文小故事，"
    "以篇為單位講解原文與直譯，語氣平穩清晰，不要加入過多誇張笑料，"
    "專注於文本本體，適合睡前聆聽。"
)

def ensure_directories():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    WEB_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

def interactive_login():
    """
    提供互動式登入模式，啟動可見瀏覽器讓使用者登入 Google 帳號，
    Session 會永久快取在 .notebooklm_session/ 目錄中。
    """
    ensure_directories()
    print("\n" + "=" * 60)
    print("【啟動 Google 帳號登入程序】")
    print("瀏覽器視窗將會打開，請在視窗中登入您的 Google 帳號。")
    print("登入成功並進入 NotebookLM 主頁後，腳本會自動儲存憑證並關閉。")
    print("=" * 60 + "\n")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(NOTEBOOKLM_URL, wait_until="domcontentloaded")

        print(">> 請在瀏覽器中完成登入... 正在監測登入狀態（最長等候 300 秒）...")
        
        # 輪詢檢測是否已成功登入進入 NotebookLM
        logged_in = False
        start_time = time.time()
        while time.time() - start_time < 300:
            current_url = page.url
            if "accounts.google.com" not in current_url and "notebooklm.google.com" in current_url:
                # 檢查頁面上是否有登入後的元素
                try:
                    if page.locator("button:has-text('New notebook'), button:has-text('新建筆記本'), [aria-label*='Create'], .create-new-notebook").count() > 0:
                        logged_in = True
                        break
                except Exception:
                    pass
            page.wait_for_timeout(2000)

        if logged_in:
            print("\n🎉 成功檢測到 Google 帳號已登入，Session 憑證已持久化保存！")
        else:
            print("\n⚠️ 登入未完成或已超時。若您已登入，下次執行仍可直接使用已保存之 Cookie。")

        context.close()

def run_automation(markdown_file_path: Path, custom_prompt: str, headless: bool = False):
    """
    自動化主流程：建立筆記本 -> 上傳文本 -> 設定 Custom Prompt -> 生成音檔 -> 下載
    """
    ensure_directories()
    
    if not markdown_file_path.exists():
        raise FileNotFoundError(f"找不到文言文檔案：{markdown_file_path}")

    markdown_content = markdown_file_path.read_text(encoding="utf-8")
    book_title = markdown_file_path.stem.replace("_", " ").title()

    print(f"\n=======================================================")
    print(f"📖 準備處理文言文文本：{markdown_file_path.name}")
    print(f"🎙️ 自訂音訊提示詞：\n   「{custom_prompt}」")
    print(f"=======================================================\n")

    with sync_playwright() as p:
        print(f">> 正在啟動 Chromium 瀏覽器（無頭模式: {headless}）...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=headless,
            viewport={"width": 1400, "height": 960},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        page = context.pages[0] if context.pages else context.new_page()

        # 1. 訪問 NotebookLM
        print(">> 正在連線至 Google NotebookLM 首頁...")
        page.goto(NOTEBOOKLM_URL, wait_until="networkidle", timeout=60000)

        # 檢查是否需要登入
        if "accounts.google.com" in page.url:
            print("\n❌ 偵測到目前尚未登入 Google 帳號！")
            print("請先執行指令：python3 scripts/notebooklm_automator.py --login 進行一次性登入。")
            context.close()
            return False

        page.wait_for_timeout(3000)

        # 2. 建立新 Notebook
        print(">> 正在點擊「新建筆記本 / New Notebook」...")
        create_btn = page.locator("button:has-text('New notebook'), button:has-text('新建筆記本'), [aria-label*='Create notebook'], button.create-button").first
        
        if create_btn.count() == 0:
            # 嘗試找包含加號圖標的按鈕
            create_btn = page.locator("button:has(svg), mat-card:has-text('New')").first
            
        if create_btn.count() > 0:
            create_btn.click()
        else:
            print("⚠️ 未直接找到新建按鈕，嘗試點擊畫面上任意新建入口...")
            page.click("text='New notebook'", timeout=10000)

        page.wait_for_timeout(5000)
        print(f">> 成功進入筆記本！目前網址: {page.url}")

        # 3. 上傳 / 貼上文言文文本來源
        print(f">> 正在將《{markdown_file_path.name}》加入筆記本來源...")
        
        # 優先尋找「Copied text / 複製的文字」或者直接上傳檔案
        copied_text_btn = page.locator("button:has-text('Copied text'), button:has-text('複製的文字'), div:has-text('Copied text')").first
        file_upload_input = page.locator("input[type='file']").first

        if copied_text_btn.count() > 0:
            print(">> 選擇「複製貼上文本」模式注入文言文結構資料...")
            copied_text_btn.click()
            page.wait_for_timeout(2000)

            # 填入文字
            textarea = page.locator("textarea, [contenteditable='true']").first
            textarea.fill(markdown_content)
            page.wait_for_timeout(1000)

            # 填入來源標題（如果有的話）
            title_input = page.locator("input[placeholder*='Title'], input[aria-label*='Title']").first
            if title_input.count() > 0:
                title_input.fill(f"國中會考文言文_{book_title}")

            # 點擊插入按鈕
            insert_btn = page.locator("button:has-text('Insert'), button:has-text('插入'), button:has-text('Done')").first
            insert_btn.click()
        elif file_upload_input.count() > 0:
            print(">> 透過檔案選擇器上傳 Markdown 檔案...")
            file_upload_input.set_input_files(str(markdown_file_path))
        else:
            print("⚠️ 尋找上傳入口，嘗試通用的來源新增按鈕...")
            page.keyboard.press("Escape")
            page.wait_for_timeout(2000)

        # 等候來源處理完成
        print(">> 等候來源處理與向量化分析完成...")
        page.wait_for_timeout(10000)

        # 4. 前往 Studio / Audio Overview (語音總覽)
        print(">> 正在定位 Audio Overview (語音總覽) 面板...")
        
        # 尋找自訂提示詞按鈕 (Customize / 自訂)
        customize_btn = page.locator(
            "button:has-text('Customize'), button:has-text('自訂'), "
            "[aria-label*='Customize'], button:has-text('自定義')"
        ).first

        if customize_btn.count() > 0:
            print(">> 找到自訂語音總覽設定按鈕，正在點擊進入...")
            customize_btn.click()
            page.wait_for_timeout(2000)

            # 填入自訂提示詞
            prompt_input = page.locator("textarea[placeholder*='focus'], textarea[aria-label*='Custom'], textarea").first
            if prompt_input.count() > 0:
                print(f">> 正在寫入睡眠解說客製化指令...")
                prompt_input.fill(custom_prompt)
                page.wait_for_timeout(1000)

            # 點擊生成按鈕
            generate_btn = page.locator("button:has-text('Generate'), button:has-text('產生'), button:has-text('生成')").first
            if generate_btn.count() > 0:
                generate_btn.click()
                print(">> 🚀 已成功點擊【產生 (Generate)】語音總覽！")
        else:
            # 若無獨立自訂按鈕，尋找標準 Generate 按鈕
            std_gen_btn = page.locator("button:has-text('Generate'), button:has-text('產生')").first
            if std_gen_btn.count() > 0:
                std_gen_btn.click()
                print(">> 🚀 已點擊生成語音總覽！")
            else:
                print("⚠️ 請確認畫面上是否有 Audio Overview 生成按鈕。")

        # 5. 輪詢等候音訊生成完成
        print("\n>> ⏳ 正在等候 NotebookLM 生成雙主持人對話音檔（通常需 3-6 分鐘，請耐心等候）...")
        audio_ready = False
        start_wait = time.time()
        timeout_seconds = 600  # 10 分鐘超時

        downloaded_file = None

        while time.time() - start_wait < timeout_seconds:
            elapsed = int(time.time() - start_wait)
            print(f"   [進度] 已等候 {elapsed // 60} 分 {elapsed % 60} 秒...", end="\r")

            # 檢查是否有播放鍵或下載按鈕出現
            download_btn = page.locator(
                "button:has-text('Download'), [aria-label*='Download'], "
                "button[aria-label*='下載'], button:has-text('下載')"
            ).first
            
            play_btn = page.locator("audio, button[aria-label*='Play'], button[aria-label*='播放']").first

            if download_btn.count() > 0 or play_btn.count() > 0:
                print(f"\n🎉 偵測到音訊已生成完畢！（總耗時：{elapsed} 秒）")
                audio_ready = True
                
                # 準備接收下載
                if download_btn.count() > 0:
                    try:
                        with page.expect_download(timeout=30000) as download_info:
                            download_btn.click()
                        download = download_info.value
                        
                        target_filename = f"{markdown_file_path.stem}.mp3"
                        target_path = AUDIO_DIR / target_filename
                        web_target_path = WEB_AUDIO_DIR / target_filename
                        
                        download.save_as(str(target_path))
                        # 同步複製一份至 web/audio/
                        download.save_as(str(web_target_path))
                        
                        downloaded_file = target_path
                        print(f"✅ 音檔已成功自動下載至：\n   - {target_path}\n   - {web_target_path}")
                        break
                    except Exception as e:
                        print(f"⚠️ 點擊下載事件捕獲異常，嘗試直接獲取 Audio 標籤網址: {e}")

                # 嘗試從 DOM 中獲取 audio src
                audio_tag = page.locator("audio source, audio").first
                if audio_tag.count() > 0:
                    src = audio_tag.get_attribute("src")
                    if src and src.startswith("http"):
                        print(f"🔗 獲取到音訊直鏈：{src}")
                        break

            page.wait_for_timeout(10000)

        if not audio_ready:
            print("\n⚠️ 等候超時（超過 10 分鐘）。音訊可能仍在排隊生成中，您可稍後再次檢查。")

        context.close()
        return True

def main():
    parser = argparse.ArgumentParser(description="國中會考文言文 NotebookLM 自動化語音總覽生成工具")
    parser.add_argument("--login", action="store_true", help="啟動互動式瀏覽器進行 Google 帳號一次性登入保存")
    parser.add_argument("--file", type=str, default=str(DATA_DIR / "shishuo_xinyu_classics.md"), help="要上傳的文言文 Markdown 檔案路徑")
    parser.add_argument("--prompt", type=str, default=DEFAULT_PROMPT, help="傳送給 NotebookLM 的自訂語音生成提示詞")
    parser.add_argument("--headless", action="store_true", help="以無介面 (headless) 模式執行（需已先完成登入）")

    args = parser.parse_args()

    if args.login:
        interactive_login()
    else:
        file_path = Path(args.file)
        run_automation(markdown_file_path=file_path, custom_prompt=args.prompt, headless=args.headless)

if __name__ == "__main__":
    main()
