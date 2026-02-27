/**
 * Popup script. "Open chat panel" sends a message to the active tab's content script to toggle the slide-in panel.
 * Uses chrome.tabs.query + chrome.tabs.sendMessage so the content script receives the action directly.
 */
document.getElementById('open-panel').addEventListener('click', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs[0];
    if (!tab?.id) {
      window.close();
      return;
    }
    chrome.tabs.sendMessage(tab.id, { action: 'togglePanel' }, (response) => {
      if (chrome.runtime.lastError) {
        console.warn('SOP Copilot popup:', chrome.runtime.lastError.message, '(content script may not be loaded on this page)');
      }
      window.close();
    });
  });
});
