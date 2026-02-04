/**
 * Service worker (Manifest V3). Stores API base; relays popup → content; proxies /chat so CORS works on all sites.
 */
const API_BASE = 'http://localhost:8000';

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({ apiBase: API_BASE });
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'togglePanel') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]?.id) chrome.tabs.sendMessage(tabs[0].id, { action: 'togglePanel' });
      sendResponse({ ok: true });
    });
    return true;
  }
  // Proxy chat from content script so request origin is extension (CORS allowed by backend)
  if (msg.action === 'chat' && typeof msg.message === 'string') {
    fetch(API_BASE + '/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg.message }),
    })
      .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
      .then(sendResponse)
      .catch((err) => sendResponse({ ok: false, data: { reply: '', error: String(err.message) } }));
    return true;
  }
});
