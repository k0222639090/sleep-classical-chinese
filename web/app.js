/**
 * 國中會考文言文睡眠廣播 (Bedtime Classical Chinese Audio Player)
 * 核心應用邏輯與音訊引擎 - UI/UX 設計師高階版
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

  // 睡眠定時器狀態
  let sleepTimer = {
    mode: null,          // null, 'end_of_track', or 'countdown'
    totalSeconds: 0,
    remainingSeconds: 0,
    intervalId: null,
    baseVolume: 1.0,
    fadeDuration: 30     // 最後 30 秒平滑淡出音量
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

  // Player headers
  const playerTrackTitle = document.getElementById('playerTrackTitle');
  const playerTrackCategory = document.getElementById('playerTrackCategory');
  const playerTrackAuthor = document.getElementById('playerTrackAuthor');
  const playerCoverText = document.getElementById('playerCoverText');
  const playerCoverSub = document.getElementById('playerCoverSub');

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
  const timerOptionButtons = document.querySelectorAll('.timer-opt-btn');

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
  // 播放器核心功能 (Audio Engine - 低記憶體網路串流架構)
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

    // 釋放先前可能佔用的音訊緩衝區，極大化減少記憶體佔用
    audio.pause();
    audio.removeAttribute('src');
    audio.load();

    // 重新指向網路音訊直鏈 (純連網串流，不佔據本機過多 RAM)
    audio.src = ep.audio_src;
    audio.playbackRate = playbackRate;
    audio.currentTime = 0;
    updateProgressUI(0, 0);

    // 更新清單高亮
    updatePlaylistActiveState();

    // 更新 MediaSession (支援手機鎖定畫面控制)
    updateMediaSession(ep);

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
    }).catch(err => {
      console.warn('自動播放被瀏覽器阻擋，需使用者互動點擊:', err);
      isPlaying = false;
      btnPlayPause.textContent = '▶';
      mainPlayerCard.classList.remove('is-playing');
    });
  }

  function pauseAudio() {
    audio.pause();
    isPlaying = false;
    btnPlayPause.textContent = '▶';
    btnPlayPause.title = '播放';
    mainPlayerCard.classList.remove('is-playing');
    updatePlaylistActiveState();
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
        const cleanTerm = ann.term.replace(/\*/g, '');
        const regex = new RegExp(`(${cleanTerm})`, 'g');
        processedText = processedText.replace(regex, `<span class="kw-term" data-vocab-idx="${i}" title="點擊查看釋義">$1</span>`);
      });
    }
    readingOriginalText.innerHTML = processedText;

    // 關鍵字詞注釋卡片網格
    readingVocabGrid.innerHTML = '';
    if (ep.annotations && ep.annotations.length > 0) {
      ep.annotations.forEach((ann, i) => {
        const card = document.createElement('div');
        card.className = 'vocab-card';
        card.id = `vocab-card-${i}`;
        card.innerHTML = `
          <div class="vocab-term-row">
            <span class="vocab-term">${ann.term}</span>
          </div>
          <div class="vocab-note">${ann.note}</div>
        `;
        readingVocabGrid.appendChild(card);
      });
    } else {
      readingVocabGrid.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem;">本篇注釋已融入直譯說明中。</p>';
    }

    // 原文點擊字詞：彈出即時注釋氣泡 (Word Popover)
    readingOriginalText.querySelectorAll('.kw-term').forEach(el => {
      el.addEventListener('click', (e) => {
        e.stopPropagation();
        const idx = el.getAttribute('data-vocab-idx');
        const ann = ep.annotations[idx];
        if (!ann) return;

        showWordPopover(el, ann.term, ann.note, idx);
      });
    });

    // 白話文直譯
    readingTranslationText.textContent = ep.translation;

    // 會考核心素養
    readingExamPointsText.textContent = ep.key_points || '深化文言實詞與古今異義辨析，把握人物言行與儒道精神涵養。';
  }

  // 浮動注釋氣泡邏輯
  function showWordPopover(targetEl, term, note, idx) {
    popoverTerm.textContent = term;
    popoverNote.innerHTML = note + `<br><a href="#vocab-card-${idx}" style="color: var(--accent-gold); font-size: 0.75rem; text-decoration: underline; margin-top: 4px; display: inline-block;">查看下方詳細考點 ➜</a>`;

    const boxRect = originalBoxContainer.getBoundingClientRect();
    const elRect = targetEl.getBoundingClientRect();

    let top = elRect.bottom - boxRect.top + 8;
    let left = elRect.left - boxRect.left;

    // 邊界防溢出處理
    if (left + 280 > boxRect.width) {
      left = Math.max(10, boxRect.width - 290);
    }

    wordPopover.style.top = `${top}px`;
    wordPopover.style.left = `${left}px`;
    wordPopover.classList.add('show');
  }

  function hideWordPopover() {
    if (wordPopover) {
      wordPopover.classList.remove('show');
    }
  }

  // 字體放大縮小
  function adjustFontSize(delta) {
    fontSizeLevel = Math.max(-1, Math.min(3, fontSizeLevel + delta));
    const fontSizes = ['1.05rem', '1.25rem', '1.45rem', '1.65rem', '1.85rem'];
    readingOriginalText.style.fontSize = fontSizes[fontSizeLevel + 1];
    readingTranslationText.style.fontSize = `calc(${fontSizes[fontSizeLevel + 1]} - 0.2rem)`;
  }

  // ==========================================
  // 播放清單與分類篩選 (Playlist System)
  // ==========================================
  function renderPlaylist() {
    playlistItemsContainer.innerHTML = '';
    playlistCount.textContent = `(共 ${filteredEpisodes.length} 篇)`;

    filteredEpisodes.forEach((ep, index) => {
      const item = document.createElement('div');
      item.className = 'playlist-item';
      if (index === currentIndex) item.classList.add('active');

      const isToday = index === 0;

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
        <div class="item-playing-indicator">
          <div class="bar"></div>
          <div class="bar"></div>
          <div class="bar"></div>
        </div>
      `;

      item.addEventListener('click', () => {
        selectEpisode(index, true);
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
  // 智慧睡眠定時器 (Sleep Timer with 30s Gentle Fade-Out)
  // ==========================================
  function setSleepTimer(minutes) {
    clearInterval(sleepTimer.intervalId);
    sleepTimer.intervalId = null;
    audio.volume = sleepTimer.baseVolume;

    if (minutes === 'off') {
      sleepTimer.mode = null;
      sleepTimerBadgeText.textContent = '睡眠定時: 關閉';
      btnOpenSleepTimer.classList.remove('active');
      timerOptionButtons.forEach(b => b.classList.toggle('active', b.dataset.minutes === 'off'));
      closeModal();
      return;
    }

    if (minutes === 'end_of_track') {
      sleepTimer.mode = 'end_of_track';
      sleepTimerBadgeText.textContent = '⏱️ 本篇播完即停';
      btnOpenSleepTimer.classList.add('active');
      timerOptionButtons.forEach(b => b.classList.toggle('active', b.dataset.minutes === 'end_of_track'));
      closeModal();
      return;
    }

    const mins = parseInt(minutes, 10);
    sleepTimer.mode = 'countdown';
    sleepTimer.totalSeconds = mins * 60;
    sleepTimer.remainingSeconds = mins * 60;
    btnOpenSleepTimer.classList.add('active');
    timerOptionButtons.forEach(b => b.classList.toggle('active', parseInt(b.dataset.minutes, 10) === mins));

    updateTimerDisplay();

    sleepTimer.intervalId = setInterval(() => {
      sleepTimer.remainingSeconds--;

      // 最後 30 秒自動柔和漸弱音量 (Gentle Audio Fade-Out)
      if (sleepTimer.remainingSeconds <= sleepTimer.fadeDuration && sleepTimer.remainingSeconds > 0) {
        const factor = sleepTimer.remainingSeconds / sleepTimer.fadeDuration;
        audio.volume = Math.max(0, sleepTimer.baseVolume * factor);
      }

      if (sleepTimer.remainingSeconds <= 0) {
        clearInterval(sleepTimer.intervalId);
        pauseAudio();
        audio.volume = sleepTimer.baseVolume;
        sleepTimer.mode = null;
        sleepTimerBadgeText.textContent = '睡眠定時: 已關閉';
        btnOpenSleepTimer.classList.remove('active');
      } else {
        updateTimerDisplay();
      }
    }, 1000);

    closeModal();
  }

  function updateTimerDisplay() {
    const m = Math.floor(sleepTimer.remainingSeconds / 60);
    const s = sleepTimer.remainingSeconds % 60;
    sleepTimerBadgeText.textContent = `⏱️ ${m}:${s.toString().padStart(2, '0')} 後休眠`;
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
  // MediaSession API (鎖定螢幕與通知控制)
  // ==========================================
  function updateMediaSession(ep) {
    if ('mediaSession' in navigator) {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: ep.title,
        artist: '睡前聽國文 · ' + ep.dynasty + ' ' + ep.author,
        album: ep.category,
        artwork: [
          { src: 'assets/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'assets/icon-512.png', sizes: '512x512', type: 'image/png' }
        ]
      });

      navigator.mediaSession.setActionHandler('play', () => playAudio());
      navigator.mediaSession.setActionHandler('pause', () => pauseAudio());
      navigator.mediaSession.setActionHandler('previoustrack', () => playPrev());
      navigator.mediaSession.setActionHandler('nexttrack', () => playNext());
      navigator.mediaSession.setActionHandler('seekbackward', () => rewind15());
      navigator.mediaSession.setActionHandler('seekforward', () => forward15());
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

    audio.addEventListener('ended', () => {
      if (sleepTimer.mode === 'end_of_track') {
        pauseAudio();
        sleepTimer.mode = null;
        sleepTimerBadgeText.textContent = '睡眠定時: 已關閉';
        btnOpenSleepTimer.classList.remove('active');
      } else {
        playNext();
      }
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

    // 定時器彈窗
    btnOpenSleepTimer.addEventListener('click', openModal);
    btnCloseSleepTimer.addEventListener('click', closeModal);
    sleepTimerModal.addEventListener('click', (e) => {
      if (e.target === sleepTimerModal) closeModal();
    });

    timerOptionButtons.forEach(btn => {
      btn.addEventListener('click', () => setSleepTimer(btn.dataset.minutes));
    });

    // OLED 模式
    btnToggleOled.addEventListener('click', toggleOledMode);
  }

  // 頁面加載就緒
  document.addEventListener('DOMContentLoaded', init);

})();
