# 國中會考文言文睡眠廣播系統 (Bedtime Classical Chinese Broadcast & Automation)

專為國中學生睡前聆聽打造的「文言文精細解說音檔與沈浸式網頁播放器」全自動化專案。以篇為單位，逐篇深度解讀原文、生難字詞注釋與精確白話直譯；語氣客觀平穩、文質彬彬，搭配極致護眼的暗夜美學與智慧睡眠定時器，陪伴學子在每晚就寢前自然涵養文言文語感與核心素養。

---

## 🌟 系統亮點特色

### 1. 結構化文言文語料庫 (High-Yield Classical Corpus)
- 精選國中教育會考高頻必考經典：
  - **《世說新語》名士特輯**（王羲之坦腹東床、王藍田食雞子、謝安雪夜詠絮、管寧割席、楊修絕妙好辭、荀巨伯遠看朋友、陳太丘與友期行、周處除三害）
  - **先秦諸子哲理與寓言特輯**（韓非子買櫝還珠、列子杞人憂天）
- 嚴格結構化：每篇皆包含【篇名】、【原文】、【關鍵字詞注釋】、【白話文直譯】與【會考素養提要與核心寓意】。

### 2. 第一階段：NotebookLM 全自動串接腳本 (`scripts/notebooklm_automator.py`)
- **免手動自動化流程**：基於 Playwright 瀏覽器自動化技術。
- **Google 帳號持久化 Session**：登入憑證持久快取於本機 `.notebooklm_session/` 目錄，往後自動化完全免重複手動登入、無懼 2FA 與機器人防護驗證。
- **自動化建立與上傳**：自動登入 NotebookLM、自動新建筆記本、自動注入文言文結構 Markdown 文本。
- **客製化語音提示詞 (Custom Prompt)**：
  > *「請兩位主持人逐篇詳細介紹文件中的每一個文言文小故事，以篇為單位講解原文與直譯，語氣平穩清晰，不要加入過多誇張笑料，專注於文本本體，適合睡前聆聽。」*
- **自動等候與下載**：智慧輪詢音訊生成狀態，完成後自動下載 MP3 音檔並同步儲存至專案 `audio/` 與網頁播放器 `web/audio/`。

### 3. 第二階段：Celestial Night 極致護眼睡眠網頁播放器 (`web/`)
- **星空暗夜與 OLED 純黑雙模式**：
  - 預設深邃午夜藍灰（#070b14）搭配靜謐月光金（#f6c453）與琥珀微光，不刺眼、無眩光。
  - 一鍵切換 **OLED 零藍光極致暗屏模式 (Night Shield)**，屏幕對比柔和微光，適合床頭暗室。
- **核心播放功能**：
  - 支援播放/暫停、自訂平滑進度條（支援直接點擊/拖曳快尋）。
  - 快退 15 秒（↺ 15）與快進 15 秒（15 ↻），方便反覆揣摩文言字句。
  - 專屬倍速：`0.8x 舒緩放鬆`、`1.0x 標準清晰`、`1.2x 溫習記憶`。
  - 分類篩選標籤：全部篇章、《世說新語》、先秦諸子。
- **智慧睡眠定時器 (Sleep Timer with 30s Audio Fade-Out)**：
  - 支援預設 `15 分鐘`、`30 分鐘`、`45 分鐘`、`60 分鐘` 以及 `播完當前篇章後停止 (End of Episode)`。
  - **獨家平滑淡出技術**：倒數進入最後 30 秒時，系統自動將音量以線性緩慢漸弱至靜音後暫停，杜絕突然中斷驚醒夢中學生的困擾。
- **圖文對照與互動注釋區**：
  - 播放時同步展示古雅大字原文（可隨時 A- / A+ 縮放字體）。
  - **原文詞彙互動聯動**：原文中的重點詞彙帶有微光底線，點擊即自動平滑捲動至對應注釋卡片並高亮提示！
  - 逐句白話直譯卡片與會考素養提要重點。
- **PWA (Progressive Web App) & MediaSession 全端適配**：
  - 支援 iPhone (Safari 加入主畫面) 與 Android / 桌面 Chrome 原生安裝為獨立 App。
  - 支援手機鎖定畫面、控制中心與 Apple Watch 顯示封面、篇名與播放跳轉。

---

## 📁 專案目錄結構

```text
睡前聽國文/
├── README.md                      # 專案操作與開發指南手冊
├── data/                          # 結構化文言文語料庫
│   ├── shishuo_xinyu_classics.md  # 《世說新語》會考高頻精細文本 (原文/注釋/直譯/提要)
│   ├── zhuzi_fables.md            # 先秦諸子百家哲理寓言文本
│   └── episodes.json              # 前端播放器結構化索引資料
├── scripts/                       # 自動化與語音生成腳本
│   ├── notebooklm_automator.py    # Playwright 自動串接 NotebookLM 登入/生成/下載
│   ├── generate_audio_tts.py      # 本地高音質睡前神經語音合成 (Edge-TTS 備援)
│   ├── text_to_json.py            # 將文言文 Markdown 轉為播放器 JSON
│   └── serve.py                   # 一鍵啟動本地 Web 播放器伺服器
├── audio/                         # 生成之文言文 MP3 音檔儲存庫
├── web/                           # 睡眠播放器前端專案
│   ├── index.html                 # 播放器核心頁面
│   ├── styles.css                 # Celestial Night 暗夜護眼設計系統
│   ├── app.js                     # 核心播放引擎、睡眠定時器與互動注釋邏輯
│   ├── manifest.json              # PWA 應用設定
│   ├── sw.js                      # Service Worker 離線快取
│   ├── episodes.json              # 網頁資料源
│   ├── assets/                    # 應用圖示 (icon-192, icon-512)
│   └── audio/                     # 供網頁直連串流之 MP3 目錄
```

---

## 🚀 快速上手使用指引

### 步驟 1：啟動網頁播放器

直接在專案根目錄執行啟動腳本：

```bash
python3 scripts/serve.py
```

或使用 Python 原生伺服器：

```bash
cd web && python3 -m http.server 8080
```

瀏覽器打開 `http://localhost:8080`，即可立即開始聆聽與閱讀！

---

### 步驟 2：執行 NotebookLM 自動化語音總覽

#### 2.1 首次使用：登入 Google 帳號 (一次性)
在終端機執行互動式登入指令：

```bash
python3 scripts/notebooklm_automator.py --login
```
瀏覽器將會彈出，請在視窗中登入您的 Google 帳號。成功登入並進入 NotebookLM 主頁後，系統會自動快取 Session，往後無需重複登入。

#### 2.2 執行全自動生成與音檔下載
登入完成後，直接執行全自動工作流程：

```bash
# 使用預設的《世說新語》文本與睡前自訂 Prompt
python3 scripts/notebooklm_automator.py

# 也可以指定背景無介面執行
python3 scripts/notebooklm_automator.py --headless

# 或指定其他文言文文本
python3 scripts/notebooklm_automator.py --file data/zhuzi_fables.md
```
腳本將自動：
1. 建立全新筆記本
2. 注入文言文 Markdown 文本
3. 填寫客製化睡前解說 Prompt
4. 等候生成完畢並自動將 MP3 下載至 `audio/` 與 `web/audio/`！

---

### 步驟 3：本地高音質睡前語音即時合成 (免等候備援)

專案內建支援微軟神經語音合成引擎，採用台灣溫柔國語女聲 (`zh-TW-HsiaoChenNeural`)，微降語速 10%，適合直接批次合成音檔：

```bash
# 合成全部篇章音檔
python3 scripts/generate_audio_tts.py 10
```

---

## 🛠️ 開發與自訂

- **新增文言文篇章**：只需在 `data/` 下編輯或新增 `.md` 檔案，維持標準的 `【篇名】`、`【原文】`、`【關鍵字詞注釋】`、`【白話文直譯】` 格式，接著執行：
  ```bash
  python3 scripts/text_to_json.py
  ```
  資料即會同步至網頁播放器。

---

*祝每位莘莘學子夜夜好眠，會考文言文輕鬆奪 A++！*
