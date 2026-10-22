#!/bin/bash
# ==============================================================================
# run_and_push.sh
# 每日文言文自動更新與 GitHub 雲端推送腳本
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "=========================================================="
echo "🌙 [$(date '+%Y-%m-%d %H:%M:%S')] 執行每日文言文睡眠篇章更新..."
echo "=========================================================="

# 執行每日更新引擎
/usr/bin/python3 scripts/daily_updater.py >> scripts/daily_update.log 2>&1

# 檢查是否有新增篇章與音檔
git add docs/ web/ data/ audio/

if git diff --staged --quiet; then
    echo "✨ [$(date '+%Y-%m-%d %H:%M:%S')] 今日篇章已就緒，無須重複推送。" >> scripts/daily_update.log
else
    git commit -m "🌙 [Auto-Update] 今日文言文睡眠篇章已自動上線 ($(date +'%Y-%m-%d'))" >> scripts/daily_update.log 2>&1
    git push origin main >> scripts/daily_update.log 2>&1
    echo "🚀 [$(date '+%Y-%m-%d %H:%M:%S')] 成功推送新篇章至 GitHub Pages 網站！" >> scripts/daily_update.log
fi
