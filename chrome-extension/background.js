chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({ apiBase: 'http://localhost:8000' });
});
