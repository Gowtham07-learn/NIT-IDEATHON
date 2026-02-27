document.getElementById('openSidebar').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  chrome.tabs.sendMessage(tab.id, { action: 'toggleSidebar' });
  window.close();
});

document.getElementById('capturePage').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  try {
    const dataUrl = await chrome.tabs.captureVisibleTab(null, { format: 'png' });
    await chrome.storage.local.set({ lastScreenshot: dataUrl });
    chrome.tabs.sendMessage(tab.id, { action: 'toggleSidebar', withScreenshot: true });
  } catch (e) {
    console.error('Screenshot failed:', e);
  }
  window.close();
});
