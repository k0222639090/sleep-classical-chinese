/**
 * 麥麥睡前聽國文 (Miley Bedtime Classical Chinese Audio Player)
 * 核心應用邏輯與音訊引擎 - UI/UX 設計師高階版
 * 具備：
 * 1. 鎖定螢幕與背景播放 (Mobile Background / Screen-off Playback)
 * 2. 播完指定篇章自動停止 / 連播 N 篇排程 (Queue / Stop after target episode)
 * 3. 30 秒智慧平滑音量淡出 (Gentle Audio Fade-Out)
 * 4. 點詞浮動注釋氣泡 (Word Popover)
 * 5. OLED 純黑深邃護眼模式 (Night Shield)
 */

(function () {
  'use strict';

  // ==========================================
  // 全域狀態 (State Management)
  // ==========================================
  let episodes = [];
  let filteredEpisodes = [];
  let currentIndex = 0;
  let isPlaying = false;
  let playbackRate = 1.0;
  let currentCategory = 'ALL';
  let fontSizeLevel = 0; // -1, 0, 1, 2, 3

  // 睡眠定時器狀態 (時間倒數模式)
  let sleepTimer = {
    mode: null,          // null, 'countdown'
    totalSeconds: 0,
    remainingSeconds: 0,
    intervalId: null,
    baseVolume: 1.0,
    fadeDuration: 30     // 最後 30 秒平滑淡出音量
  };

  // 定篇停止與連播排程狀態 (篇數 / 指定篇終點模式)
  let stopPlan = {
    type: null,          // null, 'episodes_count', 'target_episode_id'
    targetEpisodeId: null,
    targetEpisodeTitle: '',
    initialEpisodesCount: 0,
    remainingEpisodes: 0
  };

  // ==========================================
  // DOM 元素快取
  // ==========================================
  const audio = document.getElementById('audioEngine');
  const mainPlayerCard = document.getElementById('mainPlayerCard');

  // Player controls
  const btnPlayPause = document.getElementById('btnPlayPause');
  const btnPrev = document.getElementById('btnPrev');
  const btnNext = document.getElementById('btnNext');
  const btnRewind = document.getElementById('btnRewind');
  const btnForward = document.getElementById('btnForward');
  const speedButtons = document.querySelectorAll('.speed-btn');

  // Progress bar
  const progressWrapper = document.getElementById('progressWrapper');
  const progressFill = document.getElementById('progressFill');
  const progressThumb = document.getElementById('progressThumb');
  const timeCurrent = document.getElementById('timeCurrent');
  const timeDuration = document.getElementById('timeDuration');

  // Player headers & cover
  const playerTrackTitle = document.getElementById('playerTrackTitle');
  const playerTrackCategory = document.getElementById('playerTrackCategory');
  const playerTrackAuthor = document.getElementById('playerTrackAuthor');
  const playerCoverText = document.getElementById('playerCoverText');
  const playerCoverSub = document.getElementById('playerCoverSub');

  // Queue plan alert
  const queuePlanAlert = document.getElementById('queuePlanAlert');
  const queuePlanText = document.getElementById('queuePlanText');
  const btnCancelQueuePlan = document.getElementById('btnCancelQueuePlan');

  // Playlist
  const playlistItemsContainer = document.getElementById('playlistItems');
  const playlistCount = document.getElementById('playlistCount');
  const categoryTabs = document.getElementById('categoryTabs');

  // Reading Card elements
  const readingChapterTitle = document.getElementById('readingChapterTitle');
  const readingChapterSource = document.getElementById('readingChapterSource');
  const readingChapterAuthor = document.getElementById('readingChapterAuthor');
  const readingOriginalText = document.getElementById('readingOriginalText');
  const readingVocabGrid = document.getElementById('readingVocabGrid');
  const readingTranslationText = document.getElementById('readingTranslationText');
  const readingExamPointsText = document.getElementById('readingExamPointsText');
  const btnFontInc = document.getElementById('btnFontInc');
  const btnFontDec = document.getElementById('btnFontDec');

  // Popover elements
  const wordPopover = document.getElementById('wordPopover');
  const popoverTerm = document.getElementById('popoverTerm');
  const popoverNote = document.getElementById('popoverNote');
  const originalBoxContainer = document.getElementById('originalBoxContainer');

  // Sleep Timer elements
  const btnOpenSleepTimer = document.getElementById('btnOpenSleepTimer');
  const sleepTimerModal = document.getElementById('sleepTimerModal');
  const btnCloseSleepTimer = document.getElementById('btnCloseSleepTimer');
  const sleepTimerBadgeText = document.getElementById('sleepTimerBadgeText');
  const timerOptionButtons = document.querySelectorAll('.timer-opt-btn:not(.ep-opt-btn)');
  const episodeOptionButtons = document.querySelectorAll('.ep-opt-btn');

  // OLED Night Mode
  const btnToggleOled = document.getElementById('btnToggleOled');
  const oledIcon = document.getElementById('oledIcon');
  const oledText = document.getElementById('oledText');

  // ==========================================
  // 初始化與載入資料 (Initialization)
  // ==========================================
  async function init() {
    loadOledPreference();
    setupEventListeners();
    await loadEpisodesData();
  }

  async function loadEpisodesData() {
    try {
      const response = await fetch('episodes.json?v=' + Date.now());
      if (!response.ok) throw new Error('無法載入 episodes.json');
      const data = await response.json();
      episodes = data.episodes || [];
      filteredEpisodes = [...episodes];

      if (episodes.length > 0) {
        renderPlaylist();
        selectEpisode(0, false);
      }
    } catch (err) {
      console.error('載入資料錯誤:', err);
      playerTrackTitle.textContent = '載入篇章失敗，請確認網路連線';
    }
  }

  // ==========================================
  // 播放器核心功能 (Audio Engine - 支援背景與鎖定螢幕連播)
  // ==========================================
  function selectEpisode(index, autoPlay = true) {
    if (index < 0 || index >= filteredEpisodes.length) return;
    currentIndex = index;
    const ep = filteredEpisodes[currentIndex];

    // 更新播放器 UI
    playerTrackTitle.textContent = ep.title;
    playerTrackCategory.textContent = ep.category;
    playerTrackAuthor.textContent = `${ep.dynasty} · ${ep.author}`;
    playerCoverText.textContent = ep.short_title || '古文精選';
    playerCoverSub.textContent = ep.category.toUpperCase();

    // 更新右側圖文對照區
    renderReadingContent(ep);

    // 關鍵：直接設定同一個 audio 實例的 src，保留 iOS/Android 鎖定螢幕後背景連播權限
    audio.src = ep.audio_src;
    audio.playbackRate = playbackRate;
    audio.currentTime = 0;
    updateProgressUI(0, 0);

    // 更新清單高亮
    updatePlaylistActiveState();

    // 更新 MediaSession (鎖定螢幕專輯封面、作者與控制按鈕)
    updateMediaSession(ep);

    // 檢查篇數連播狀態更新
    updateQueuePlanDisplay();

    if (autoPlay) {
      playAudio();
    } else {
      pauseAudio();
    }
  }

  function playAudio() {
    audio.play().then(() => {
      isPlaying = true;
      btnPlayPause.textContent = '⏸';
      btnPlayPause.title = '暫停';
      mainPlayerCard.classList.add('is-playing');
      updatePlaylistActiveState();
      if ('mediaSession' in navigator) {
        navigator.mediaSession.playbackState = 'playing';
      }
    }).catch(err => {
      console.warn('自動播放被瀏覽器阻擋，需使用者互動點擊:', err);
      isPlaying = false;
      btnPlayPause.textContent = '▶';
      mainPlayerCard.classList.remove('is-playing');
      if ('mediaSession' in navigator) {
        navigator.mediaSession.playbackState = 'paused';
      }
    });
  }

  function pauseAudio() {
    audio.pause();
    isPlaying = false;
    btnPlayPause.textContent = '▶';
    btnPlayPause.title = '播放';
    mainPlayerCard.classList.remove('is-playing');
    updatePlaylistActiveState();
    if ('mediaSession' in navigator) {
      navigator.mediaSession.playbackState = 'paused';
    }
  }

  function togglePlayPause() {
    if (isPlaying) {
      pauseAudio();
    } else {
      playAudio();
    }
  }

  function playNext() {
    const nextIndex = (currentIndex + 1) % filteredEpisodes.length;
    selectEpisode(nextIndex, true);
  }

  function playPrev() {
    const prevIndex = (currentIndex - 1 + filteredEpisodes.length) % filteredEpisodes.length;
    selectEpisode(prevIndex, true);
  }

  function rewind15() {
    audio.currentTime = Math.max(0, audio.currentTime - 15);
  }

  function forward15() {
    audio.currentTime = Math.min(audio.duration || 0, audio.currentTime + 15);
  }

  function setPlaybackSpeed(speed) {
    playbackRate = parseFloat(speed);
    audio.playbackRate = playbackRate;
    speedButtons.forEach(btn => {
      btn.classList.toggle('active', parseFloat(btn.dataset.speed) === playbackRate);
    });
  }

  // ==========================================
  // 進度條與時間計算
  // ==========================================
  function updateProgressUI(current, duration) {
    timeCurrent.textContent = formatTime(current);
    timeDuration.textContent = duration ? formatTime(duration) : '--:--';

    const percentage = duration > 0 ? (current / duration) * 100 : 0;
    progressFill.style.width = percentage + '%';
    progressThumb.style.left = percentage + '%';

    // 同步鎖定畫面進度
    if ('mediaSession' in navigator && duration && duration > 0 && typeof navigator.mediaSession.setPositionState === 'function') {
      try {
        navigator.mediaSession.setPositionState({
          duration: duration,
          playbackRate: audio.playbackRate,
          position: Math.min(current, duration)
        });
      } catch (e) {}
    }
  }

  function formatTime(seconds) {
    if (isNaN(seconds) || seconds < 0) return '00:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }

  function handleSeek(e) {
    const rect = progressWrapper.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const width = rect.width;
    const ratio = Math.max(0, Math.min(1, clickX / width));
    if (audio.duration) {
      audio.currentTime = ratio * audio.duration;
      updateProgressUI(audio.currentTime, audio.duration);
    }
  }

  // ==========================================
  // 圖文對照與注釋渲染 (Reading Content + Word Popover)
  // ==========================================
  function renderReadingContent(ep) {
    readingChapterTitle.textContent = ep.short_title;
    readingChapterSource.textContent = ep.title;
    readingChapterAuthor.textContent = `${ep.dynasty} · ${ep.author}`;

    // 原文段落 (自動標注關鍵字詞並支援點擊彈出氣泡注釋)
    let processedText = ep.original_text;
    if (ep.annotations && ep.annotations.length > 0) {
      ep.annotations.forEach((ann, i) => {
        const rawTerm = ann.term.trim();
        const cleanTerm = rawTerm.split(/[（(]/)[0].replace(/[*_~`]/g, '');
        if (cleanTerm && cleanTerm.length > 0) {
          const escaped = cleanTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
          const regex = new RegExp(`(${escaped})`, 'g');
          processedText = processedText.replace(regex, `<span class="kw-term" data-idx="${i}">$1</span>`);
        }
      });
    }

    readingOriginalText.innerHTML = processedText.replace(/\n/g, '<br><br>');

    // 綁定注釋點擊彈窗
    readingOriginalText.querySelectorAll('.kw-term').forEach(el => {
      el.addEventListener('click', (e) => {
        e.stopPropagation();
        const idx = parseInt(el.dataset.idx, 10);
        showWordPopover(el, ep.annotations[idx]);
      });
    });

    // 關鍵注釋清單
    readingVocabGrid.innerHTML = '';
    if (ep.annotations && ep.annotations.length > 0) {
      ep.annotations.forEach(item => {
        const card = document.createElement('div');
        card.className = 'vocab-item';
        card.innerHTML = `
          <div class="vocab-term">${item.term}</div>
          <div class="vocab-note">${item.note}</div>
        `;
        readingVocabGrid.appendChild(card);
      });
    } else {
      readingVocabGrid.innerHTML = '<div style="color: var(--text-muted); font-size: 0.88rem;">本篇字句易懂，無特殊生難字詞。</div>';
    }

    // 白話文直譯
    readingTranslationText.textContent = ep.translation || '（暫無直譯）';

    // 會考素養核心寓意
    readingExamPointsText.textContent = ep.key_points || '（暫無素養提要）';
  }

  function showWordPopover(targetEl, annData) {
    if (!annData) return;
    popoverTerm.textContent = annData.term;
    popoverNote.textContent = annData.note;

    const rect = targetEl.getBoundingClientRect();
    const containerRect = originalBoxContainer.getBoundingClientRect();

    const top = rect.bottom - containerRect.top + 8;
    let left = rect.left - containerRect.left + (rect.width / 2) - 130;

    if (left < 10) left = 10;
    if (left + 260 > containerRect.width) left = containerRect.width - 270;

    wordPopover.style.top = top + 'px';
    wordPopover.style.left = left + 'px';
    wordPopover.classList.add('visible');
  }

  function hideWordPopover() {
    wordPopover.classList.remove('visible');
  }

  function adjustFontSize(delta) {
    fontSizeLevel = Math.max(-1, Math.min(3, fontSizeLevel + delta));
    const sizes = ['0.95rem', '1.08rem', '1.22rem', '1.38rem', '1.55rem'];
    readingOriginalText.style.fontSize = sizes[fontSizeLevel + 1];
  }

  // ==========================================
  // 播放清單渲染 (Playlist Items with Stop Target Buttons)
  // ==========================================
  function renderPlaylist() {
    playlistItemsContainer.innerHTML = '';
    playlistCount.textContent = `(共 ${filteredEpisodes.length} 篇)`;

    filteredEpisodes.forEach((ep, index) => {
      const item = document.createElement('div');
      item.className = 'playlist-item';
      if (index === currentIndex) item.classList.add('active');

      const isToday = index === 0;
      const isStopTarget = stopPlan.type === 'target_episode_id' && ep.id === stopPlan.targetEpisodeId;
      if (isStopTarget) item.classList.add('is-stop-target');

      item.innerHTML = `
        <div class="item-left">
          <div class="item-badge">${index + 1}</div>
          <div class="item-meta">
            <span class="item-title">
              ${ep.short_title}
              ${isToday ? '<span style="font-size: 0.65rem; background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16,185,129,0.3); border-radius: 9999px; padding: 1px 6px; margin-left: 4px;">今日上新</span>' : ''}
            </span>
            <span class="item-sub">${ep.category}</span>
          </div>
        </div>
        <div class="item-right-actions">
          <button class="btn-set-stop-point" data-id="${ep.id}" data-title="${ep.short_title}" title="設定播完此篇後自動休眠停止">
            ${isStopTarget ? '🛑 播完此篇停' : '🛑 設為終點'}
          </button>
          <div class="item-playing-indicator">
            <div class="bar"></div>
            <div class="bar"></div>
            <div class="bar"></div>
          </div>
        </div>
      `;

      // 點擊清單切換播放
      item.addEventListener('click', (e) => {
        if (e.target.closest('.btn-set-stop-point')) return;
        selectEpisode(index, true);
      });

      // 點擊「設為終點」按鈕
      const stopBtn = item.querySelector('.btn-set-stop-point');
      stopBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleStopTargetEpisode(ep.id, ep.short_title);
      });

      playlistItemsContainer.appendChild(item);
    });
  }

  function updatePlaylistActiveState() {
    const items = playlistItemsContainer.querySelectorAll('.playlist-item');
    items.forEach((item, index) => {
      const isActive = index === currentIndex;
      item.classList.toggle('active', isActive);
      item.classList.toggle('is-playing', isActive && isPlaying);

      const ep = filteredEpisodes[index];
      if (ep) {
        const isStopTarget = stopPlan.type === 'target_episode_id' && ep.id === stopPlan.targetEpisodeId;
        item.classList.toggle('is-stop-target', isStopTarget);
        const stopBtn = item.querySelector('.btn-set-stop-point');
        if (stopBtn) {
          stopBtn.textContent = isStopTarget ? '🛑 播完此篇停' : '🛑 設為終點';
        }
      }
    });
  }

  function filterCategory(cat) {
    currentCategory = cat;
    if (cat === 'ALL') {
      filteredEpisodes = [...episodes];
    } else {
      filteredEpisodes = episodes.filter(e => e.category === cat);
    }
    currentIndex = 0;
    renderPlaylist();
    if (filteredEpisodes.length > 0) {
      selectEpisode(0, false);
    }
  }

  // ==========================================
  // 定篇停止與連播排程控制 (Stop Plan & Queue Engine)
  // ==========================================
  function setEpisodeLimit(count) {
    // 清除既有的倒數計時器
    clearCountdownTimer();

    stopPlan = {
      type: 'episodes_count',
      targetEpisodeId: null,
      targetEpisodeTitle: '',
      initialEpisodesCount: count,
      remainingEpisodes: count
    };

    episodeOptionButtons.forEach(btn => {
      btn.classList.toggle('active', parseInt(btn.dataset.episodes, 10) === count);
    });
    timerOptionButtons.forEach(btn => btn.classList.remove('active'));

    updateQueuePlanDisplay();
    closeModal();
  }

  function toggleStopTargetEpisode(epId, epTitle) {
    clearCountdownTimer();

    if (stopPlan.type === 'target_episode_id' && stopPlan.targetEpisodeId === epId) {
      // 取消終點設定
      clearAllStopPlans();
      return;
    }

    stopPlan = {
      type: 'target_episode_id',
      targetEpisodeId: epId,
      targetEpisodeTitle: epTitle,
      initialEpisodesCount: 0,
      remainingEpisodes: 0
    };

    updateQueuePlanDisplay();
    updatePlaylistActiveState();
  }

  function updateQueuePlanDisplay() {
    if (stopPlan.type === 'episodes_count') {
      queuePlanAlert.style.display = 'flex';
      const curEpNum = stopPlan.initialEpisodesCount - stopPlan.remainingEpisodes + 1;
      queuePlanText.textContent = `🌙 連播計畫：聽 ${stopPlan.initialEpisodesCount} 篇即停 (目前正播第 ${curEpNum}/${stopPlan.initialEpisodesCount} 篇)`;
      sleepTimerBadgeText.textContent = `⏱️ 聽 ${stopPlan.initialEpisodesCount} 篇即停 (${stopPlan.remainingEpisodes}篇剩餘)`;
      btnOpenSleepTimer.classList.add('active');
    } else if (stopPlan.type === 'target_episode_id') {
      queuePlanAlert.style.display = 'flex';
      queuePlanText.textContent = `🌙 終點計畫：播完《${stopPlan.targetEpisodeTitle}》後自動休眠停止`;
      sleepTimerBadgeText.textContent = `⏱️ 播完《${stopPlan.targetEpisodeTitle}》停`;
      btnOpenSleepTimer.classList.add('active');
    } else if (sleepTimer.mode === 'countdown') {
      queuePlanAlert.style.display = 'none';
      btnOpenSleepTimer.classList.add('active');
    } else {
      queuePlanAlert.style.display = 'none';
      sleepTimerBadgeText.textContent = '睡眠關閉: 自由連播';
      btnOpenSleepTimer.classList.remove('active');
    }
  }

  function clearAllStopPlans() {
    clearCountdownTimer();
    stopPlan = {
      type: null,
      targetEpisodeId: null,
      targetEpisodeTitle: '',
      initialEpisodesCount: 0,
      remainingEpisodes: 0
    };
    episodeOptionButtons.forEach(btn => btn.classList.remove('active'));
    timerOptionButtons.forEach(btn => btn.classList.toggle('active', btn.dataset.minutes === 'off'));
    updateQueuePlanDisplay();
    updatePlaylistActiveState();
  }

  // ==========================================
  // 時間倒數定時器 (Sleep Timer with 30s Gentle Fade-Out)
  // ==========================================
  function setCountdownTimer(minutes) {
    if (minutes === 'off') {
      clearAllStopPlans();
      closeModal();
      return;
    }

    clearCountdownTimer();
    // 清除篇數排程，切換為時間倒數
    stopPlan.type = null;
    stopPlan.targetEpisodeId = null;

    const mins = parseInt(minutes, 10);
    sleepTimer.mode = 'countdown';
    sleepTimer.totalSeconds = mins * 60;
    sleepTimer.remainingSeconds = mins * 60;

    btnOpenSleepTimer.classList.add('active');
    timerOptionButtons.forEach(b => b.classList.toggle('active', parseInt(b.dataset.minutes, 10) === mins));
    episodeOptionButtons.forEach(b => b.classList.remove('active'));

    updateCountdownDisplay();

    sleepTimer.intervalId = setInterval(() => {
      sleepTimer.remainingSeconds--;

      // 最後 30 秒自動柔和漸弱音量 (Gentle Audio Fade-Out)
      if (sleepTimer.remainingSeconds <= sleepTimer.fadeDuration && sleepTimer.remainingSeconds > 0) {
        const factor = sleepTimer.remainingSeconds / sleepTimer.fadeDuration;
        audio.volume = Math.max(0, sleepTimer.baseVolume * factor);
      }

      if (sleepTimer.remainingSeconds <= 0) {
        clearInterval(sleepTimer.intervalId);
        executeGentleSleepStop('定時已到，今夜陪伴到此，祝您安然入睡 🌙');
      } else {
        updateCountdownDisplay();
      }
    }, 1000);

    closeModal();
  }

  function clearCountdownTimer() {
    if (sleepTimer.intervalId) {
      clearInterval(sleepTimer.intervalId);
      sleepTimer.intervalId = null;
    }
    sleepTimer.mode = null;
    audio.volume = sleepTimer.baseVolume;
  }

  function updateCountdownDisplay() {
    const m = Math.floor(sleepTimer.remainingSeconds / 60);
    const s = sleepTimer.remainingSeconds % 60;
    sleepTimerBadgeText.textContent = `⏱️ ${m}:${s.toString().padStart(2, '0')} 後休眠`;
  }

  // 溫柔停止並恢復音量
  function executeGentleSleepStop(noticeMsg) {
    let fadeStep = 10;
    const fadeInterval = setInterval(() => {
      fadeStep--;
      if (fadeStep <= 0) {
        clearInterval(fadeInterval);
        pauseAudio();
        audio.volume = sleepTimer.baseVolume;
        clearAllStopPlans();
        if (noticeMsg) {
          queuePlanAlert.style.display = 'flex';
          queuePlanText.textContent = `✨ ${noticeMsg}`;
          setTimeout(() => {
            queuePlanAlert.style.display = 'none';
          }, 8000);
        }
      } else {
        audio.volume = Math.max(0, sleepTimer.baseVolume * (fadeStep / 10));
      }
    }, 150);
  }

  function openModal() {
    sleepTimerModal.classList.add('open');
  }

  function closeModal() {
    sleepTimerModal.classList.remove('open');
  }

  // ==========================================
  // OLED 深邃助眠護眼模式 (Night Shield)
  // ==========================================
  function toggleOledMode() {
    const isOled = document.documentElement.classList.toggle('oled-mode');
    localStorage.setItem('sleep_classics_oled', isOled ? 'true' : 'false');
    updateOledButtonUI(isOled);
  }

  function loadOledPreference() {
    const saved = localStorage.getItem('sleep_classics_oled');
    if (saved === 'true') {
      document.documentElement.classList.add('oled-mode');
      updateOledButtonUI(true);
    }
  }

  function updateOledButtonUI(isOled) {
    if (isOled) {
      oledIcon.textContent = '🌙';
      oledText.textContent = '極致暗屏中';
      btnToggleOled.classList.add('active');
    } else {
      oledIcon.textContent = '🕯️';
      oledText.textContent = '助眠護眼';
      btnToggleOled.classList.remove('active');
    }
  }

  // ==========================================
  // MediaSession API (手機鎖定螢幕與背景播放支援)
  // ==========================================
  function updateMediaSession(ep) {
    if ('mediaSession' in navigator) {
      const coverUrl = new URL('assets/cover.png', window.location.href).href;
      const iconUrl = new URL('assets/icon-512.png', window.location.href).href;

      navigator.mediaSession.metadata = new MediaMetadata({
        title: ep.title,
        artist: '麥麥睡前聽國文',
        album: `${ep.dynasty} · ${ep.author} (${ep.category})`,
        artwork: [
          { src: coverUrl, sizes: '512x512', type: 'image/png' },
          { src: iconUrl, sizes: '512x512', type: 'image/png' }
        ]
      });

      navigator.mediaSession.setActionHandler('play', () => playAudio());
      navigator.mediaSession.setActionHandler('pause', () => pauseAudio());
      navigator.mediaSession.setActionHandler('previoustrack', () => playPrev());
      navigator.mediaSession.setActionHandler('nexttrack', () => playNext());
      navigator.mediaSession.setActionHandler('seekbackward', () => rewind15());
      navigator.mediaSession.setActionHandler('seekforward', () => forward15());
      navigator.mediaSession.setActionHandler('seekto', (details) => {
        if (details.seekTime !== undefined && details.seekTime !== null) {
          audio.currentTime = details.seekTime;
          updateProgressUI(audio.currentTime, audio.duration);
        }
      });
    }
  }

  // ==========================================
  // PWA 安裝觸發 (遵循 pwa_installer_master 規範)
  // ==========================================
  window.deferredPrompt = null;
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    window.deferredPrompt = e;
  });

  window.triggerPWAInstall = function () {
    const ua = (navigator.userAgent || '').toLowerCase();
    const isIOS = /ipad|iphone|ipod/.test(ua) && !window.MSStream;

    if (window.deferredPrompt) {
      window.deferredPrompt.prompt();
      window.deferredPrompt.userChoice.then((choice) => {
        if (choice && choice.outcome === 'accepted') {
          localStorage.setItem('sleep_classics_pwa_installed', 'true');
          document.documentElement.classList.add('is-pwa-standalone');
        }
        window.deferredPrompt = null;
      });
      return;
    }

    if (isIOS) {
      alert('📲 iPhone / iPad 請點擊 Safari 底部「分享」圖標 (帶箭頭方框) ➜ 滑動選擇「加入主畫面 ⊞」即可！');
      return;
    }

    alert('📲 請點擊瀏覽器右上角「⋮」或選單 ➜ 選擇「加到主畫面」或「安裝應用程式」即可在桌面離線收聽！');
  };

  // ==========================================
  // 事件監聽綁定 (Event Listeners)
  // ==========================================
  function setupEventListeners() {
    // 播放器按鈕
    btnPlayPause.addEventListener('click', togglePlayPause);
    btnNext.addEventListener('click', playNext);
    btnPrev.addEventListener('click', playPrev);
    btnRewind.addEventListener('click', rewind15);
    btnForward.addEventListener('click', forward15);

    // 取消排程按鈕
    btnCancelQueuePlan.addEventListener('click', clearAllStopPlans);

    // 倍速切換
    speedButtons.forEach(btn => {
      btn.addEventListener('click', () => setPlaybackSpeed(btn.dataset.speed));
    });

    // 音訊引擎事件
    audio.addEventListener('timeupdate', () => {
      updateProgressUI(audio.currentTime, audio.duration);
    });

    audio.addEventListener('loadedmetadata', () => {
      updateProgressUI(audio.currentTime, audio.duration);
    });

    // 關鍵：一首播畢時的排程判定與自動切換
    audio.addEventListener('ended', () => {
      const currentEp = filteredEpisodes[currentIndex];

      // 情況 1：已設定為特定篇章為終點
      if (stopPlan.type === 'target_episode_id' && currentEp && currentEp.id === stopPlan.targetEpisodeId) {
        executeGentleSleepStop(`《${stopPlan.targetEpisodeTitle}》已播畢，祝您好夢 🌙`);
        return;
      }

      // 情況 2：已設定連播 N 篇
      if (stopPlan.type === 'episodes_count') {
        stopPlan.remainingEpisodes--;
        if (stopPlan.remainingEpisodes <= 0) {
          executeGentleSleepStop('今夜排定之文言文篇章已全數播畢，祝您好夢 🌙');
          return;
        } else {
          updateQueuePlanDisplay();
          playNext();
          return;
        }
      }

      // 情況 3：一般自由連播
      playNext();
    });

    // 點擊頁面其他地方關閉注釋氣泡
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.kw-term') && !e.target.closest('#wordPopover')) {
        hideWordPopover();
      }
    });

    // 進度條拖曳或點擊
    progressWrapper.addEventListener('click', handleSeek);

    // 分類切換
    categoryTabs.addEventListener('click', (e) => {
      const tab = e.target.closest('.cat-tab');
      if (tab) {
        categoryTabs.querySelectorAll('.cat-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        filterCategory(tab.dataset.category);
      }
    });

    // 字體縮放
    btnFontInc.addEventListener('click', () => adjustFontSize(1));
    btnFontDec.addEventListener('click', () => adjustFontSize(-1));

    // 定時器與篇數設定彈窗
    btnOpenSleepTimer.addEventListener('click', openModal);
    btnCloseSleepTimer.addEventListener('click', closeModal);
    sleepTimerModal.addEventListener('click', (e) => {
      if (e.target === sleepTimerModal) closeModal();
    });

    // 篇數選項按鈕
    episodeOptionButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const count = parseInt(btn.dataset.episodes, 10);
        setEpisodeLimit(count);
      });
    });

    // 時間倒數選項按鈕
    timerOptionButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        setCountdownTimer(btn.dataset.minutes);
      });
    });

    // OLED 模式
    btnToggleOled.addEventListener('click', toggleOledMode);
  }

  // 頁面加載就緒
  document.addEventListener('DOMContentLoaded', init);

})();
