(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.ChatGPTTabNotifier = Object.assign(root.ChatGPTTabNotifier || {}, api);
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const PREFIX = 'fortis-observatory-v1-pair-';
  const ORIGIN = 'http://127.0.0.1:18753';

  function currentChatId(url = location.href) {
    try {
      const parsed = new URL(url);
      if (parsed.origin !== 'https://chatgpt.com' && parsed.origin !== 'https://chat.openai.com') return '';
      const match = parsed.pathname.match(/^\/c\/([A-Za-z0-9-]{8,100})\/?$/);
      return match ? match[1] : '';
    } catch (_) { return ''; }
  }

  function validatePairing(value, chatId) {
    if (!value || typeof value !== 'object' || value.version !== 1 ||
        value.origin !== ORIGIN || value.conversation_id !== chatId ||
        !/^rs_[0-9a-f]{32}$/.test(value.reporting_session_id || '') ||
        !/^[A-Za-z0-9_-]{40,70}$/.test(value.observer_key || '')) return null;
    return {
      version: 1, origin: ORIGIN, conversation_id: chatId,
      reporting_session_id: value.reporting_session_id, observer_key: value.observer_key
    };
  }

  function createObservatoryCompletionBridge({
    tabState, responseMonitor, notify = () => {}, isEnabled = () => true
  } = {}) {
    let chatId = '';
    let latestSequence = -1;
    let workStartedAt = 0;
    let requestPending = false;
    let lastCheckAt = 0;
    let pairing = null;
    let generation = 0;
    let lastTriggeredSequence = -1;
    let initialStatusRead = false;
    let startSequence = -1;
    // Old archives must not cause stale working indicators after a page reload.
    const MAX_EVENT_AGE_MS = 120000;

    function refreshChat() {
      const next = currentChatId();
      if (next === chatId) return;
      generation += 1;
      chatId = next;
      latestSequence = -1;
      lastTriggeredSequence = -1;
      initialStatusRead = false;
      startSequence = -1;
      workStartedAt = 0;
      requestPending = false;
      try {
        pairing = next && typeof GM_getValue === 'function'
          ? validatePairing(GM_getValue(PREFIX + next, null), next) : null;
      } catch (_) { pairing = null; }
    }

    function noteArmed() {
      refreshChat();
      workStartedAt = Date.now();
      startSequence = Math.max(startSequence, latestSequence);
    }

    function receive(data, snapshot) {
      if (!isEnabled() || !pairing || snapshot !== generation || currentChatId() !== chatId) return false;
      if (!data || data.ok !== true || data.version !== 1 ||
          data.conversation_id !== chatId ||
          data.reporting_session_id !== pairing.reporting_session_id ||
          !Number.isInteger(data.sequence) || data.sequence < -1 ||
          !['none', 'started', 'progress', 'checkpoint', 'blocked', 'completed', 'failed'].includes(data.event)) return false;

      const acceptedMs = typeof data.accepted_unix === 'number' ? data.accepted_unix * 1000 : 0;
      const fresh = acceptedMs > 0 && Number.isFinite(acceptedMs) &&
        acceptedMs <= Date.now() + 30000 && Date.now() - acceptedMs <= MAX_EVENT_AGE_MS;
      const initialRead = !initialStatusRead;
      initialStatusRead = true;
      if (data.sequence <= latestSequence) return false;
      latestSequence = data.sequence;
      if (!fresh) return false;

      if (['started', 'progress', 'checkpoint'].includes(data.event)) {
        // Progress is active work when a rapid started event fell between polls.
        if (startSequence < 0 || data.event === 'started' ||
            !['working', 'observatory-working'].includes(tabState?.getState?.())) {
          startSequence = data.sequence;
          workStartedAt = acceptedMs;
        }
        if (responseMonitor?.startFromExternal?.()) {
          notify('Работа начата по событию Fortis Observatory');
          return true;
        }
        return false;
      }

      if (data.event === 'completed' && !initialRead && workStartedAt > 0 &&
          acceptedMs >= workStartedAt &&
          data.sequence > Math.max(startSequence, lastTriggeredSequence) &&
          ['working', 'observatory-working'].includes(tabState?.getState?.()) &&
          responseMonitor?.finishFromExternal?.()) {
        lastTriggeredSequence = data.sequence;
        workStartedAt = 0;
        startSequence = -1;
        notify('Работа завершена по событию Fortis Observatory');
        return true;
      }
      return false;
    }

    function check() {
      refreshChat();
      if (!isEnabled() || !pairing || requestPending || typeof GM_xmlhttpRequest !== 'function') return;
      if (Date.now() - lastCheckAt < 3000) return;
      lastCheckAt = Date.now();
      requestPending = true;
      const snapshot = generation;
      try {
        GM_xmlhttpRequest({
          method: 'GET',
          url: ORIGIN + '/api/observer-status?session=' + encodeURIComponent(pairing.reporting_session_id),
          headers: { 'X-Fortis-Observer-Key': pairing.observer_key },
          timeout: 3000,
          onload(response) {
            requestPending = false;
            if (response.status !== 200) return;
            try { receive(JSON.parse(response.responseText), snapshot); } catch (_) { /* fail closed */ }
          },
          onerror() { requestPending = false; },
          ontimeout() { requestPending = false; }
        });
      } catch (_) { requestPending = false; }
    }

    function pairCurrent() {
      refreshChat();
      if (!chatId || typeof GM_setValue !== 'function') {
        alert('Открой обычную беседу /c/... для привязки.');
        return;
      }
      const raw = prompt('Вставь код привязки из Observatory (НЕ отправляй его в чат):');
      if (!raw) return;
      let candidate;
      try { candidate = validatePairing(JSON.parse(raw), chatId); } catch (_) { candidate = null; }
      if (!candidate) { alert('Код не подходит для этого Chat ID или сервера.'); return; }
      GM_setValue(PREFIX + chatId, candidate);
      generation += 1;
      pairing = candidate;
      latestSequence = -1;
      lastTriggeredSequence = -1;
      initialStatusRead = false;
      startSequence = -1;
      workStartedAt = 0;
      lastCheckAt = 0;
      check();
      alert('Привязка сохранена только для текущего Chat ID.');
    }

    function unpairCurrent() {
      refreshChat();
      if (chatId && typeof GM_deleteValue === 'function') GM_deleteValue(PREFIX + chatId);
      generation += 1;
      pairing = null;
      requestPending = false;
      workStartedAt = 0;
      startSequence = -1;
      initialStatusRead = false;
      alert('Привязка Observatory удалена для текущего чата.');
    }

    refreshChat();
    return {
      noteArmed, check, resetForNavigation: refreshChat, pairCurrent, unpairCurrent,
      isPaired: () => Boolean(pairing),
      getLatestSequence: () => latestSequence
    };
  }

  // Each chat has a separate mode per browser tab, persisted for reloads.
  const MODE_PREFIX = 'fortis-observatory-v1-completion-mode-';
  const MODES = Object.freeze(['both', 'dom', 'observatory', 'off']);

  function createCompletionModeSettings({ show = message => alert(message) } = {}) {
    let chatId = null;
    let mode = 'both';

    function syncChat() {
      const next = currentChatId();
      if (next === chatId) return;
      chatId = next;
      mode = 'both';
      if (!chatId) return;
      try {
        const stored = sessionStorage.getItem(MODE_PREFIX + chatId);
        if (MODES.includes(stored)) mode = stored;
      } catch (_) { /* fail back to original native behavior */ }
    }

    function domEnabled() {
      syncChat();
      return mode === 'both' || mode === 'dom';
    }

    function observatoryEnabled() {
      syncChat();
      return mode === 'both' || mode === 'observatory';
    }

    function describe() {
      syncChat();
      return 'Источники начала и завершения текущего чата:\n' +
        'DOM Tab Notifier: ' + (domEnabled() ? 'ВКЛ' : 'ВЫКЛ') + '\n' +
        'Fortis Observatory: ' + (observatoryEnabled() ? 'ВКЛ' : 'ВЫКЛ') + '\n\n' +
        'Отключаются НАЧАЛО и КОНЕЦ по выбранному источнику; автоотправка не меняется.\n' +
        'Для сравнения запусти новую генерацию после переключения.';
    }

    function setMode(nextMode) {
      syncChat();
      if (!chatId || !MODES.includes(nextMode)) return false;
      try {
        sessionStorage.setItem(MODE_PREFIX + chatId, nextMode);
      } catch (_) {
        show('Не удалось сохранить режим для этой вкладки.');
        return false;
      }
      mode = nextMode;
      return true;
    }

    function toggleDom() {
      const next = domEnabled()
        ? (observatoryEnabled() ? 'observatory' : 'off')
        : (observatoryEnabled() ? 'both' : 'dom');
      if (!setMode(next)) return show('Открой обычный чат /c/... для настройки.');
      show(describe());
    }

    function toggleObservatory() {
      const next = observatoryEnabled()
        ? (domEnabled() ? 'dom' : 'off')
        : (domEnabled() ? 'both' : 'observatory');
      if (!setMode(next)) return show('Открой обычный чат /c/... для настройки.');
      show(describe());
    }

    function showStatus() { show(describe()); }

    syncChat();
    return {
      domEnabled, observatoryEnabled, toggleDom, toggleObservatory,
      showStatus, getMode: () => { syncChat(); return mode; }
    };
  }

  return { createObservatoryCompletionBridge, createCompletionModeSettings,
           currentChatId, validatePairing };
});
