/**
 * SOP Copilot – content script. Injects floating button + slide-in chat panel on every page.
 * Sends POST to http://localhost:8000/chat with { "message": string }; displays reply or error.
 */

(function () {
  'use strict';

  console.log('SOP Copilot: content script loaded');

  const API_BASE = 'http://localhost:8000';
  const PANEL_ID = 'sop-copilot-panel';
  const FAB_ID = 'sop-copilot-fab';
  const ROOT_ID = 'sop-copilot-root';

  /** Ensure a single root container on document.body to avoid duplicate UI and isolate from page styles */
  function getOrCreateRoot() {
    let root = document.getElementById(ROOT_ID);
    if (root) return root;
    root = document.createElement('div');
    root.id = ROOT_ID;
    root.className = 'sop-copilot-root';
    document.body.appendChild(root);
    return root;
  }

  const PAGE_CTX_MARKER = '__SOP_PAGE_CONTEXT__';
  const USER_Q_MARKER = '__SOP_USER_QUESTION__';
  const MAX_PAGE_CHARS = 12000;

  /** Get currently selected text on the page */
  function getSelectedText() {
    const sel = window.getSelection();
    return (sel && sel.toString ? sel.toString() : '').trim();
  }

  /** Extract visible text from current page. Prefer main/article; skip scripts, nav, ads, cookie banners. */
  function extractPageContent() {
    try {
      const root = document.querySelector('main') || document.querySelector('article') ||
        document.querySelector('[role="main"]') || document.querySelector('#content') ||
        document.querySelector('.content') || document.body;
      const clone = root.cloneNode(true);
      const remove = clone.querySelectorAll(
        'script, style, noscript, iframe, svg, canvas, nav, header, footer, ' +
        '[role="navigation"], [role="banner"], [role="contentinfo"], ' +
        '.ad, .ads, .advertisement, [class*="cookie"], [id*="cookie"], ' +
        '[aria-hidden="true"], [hidden]'
      );
      remove.forEach(function (el) { el.remove(); });
      let text = (clone.innerText || clone.textContent || '').trim();
      text = text.replace(/\s+/g, ' ').replace(/ +/g, ' ').trim();
      if (text.length > MAX_PAGE_CHARS) text = text.slice(0, MAX_PAGE_CHARS) + ' [truncated]';
      return text;
    } catch (e) {
      console.warn('SOP Copilot: page extraction failed', e);
      return '';
    }
  }

  /** Create floating chat button and append to root (no duplicate if already present) */
  function createFab() {
    if (document.getElementById(FAB_ID)) return;
    const root = getOrCreateRoot();
    const fab = document.createElement('button');
    fab.id = FAB_ID;
    fab.className = 'sop-fab';
    fab.setAttribute('aria-label', 'Open SOP Copilot');
    fab.innerHTML = '&#128203;'; // clipboard emoji
    fab.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      togglePanel();
    }, true);
    root.appendChild(fab);
    console.log('SOP Copilot: button injected');
  }

  /** Create slide-in panel with header (draggable), messages, input; append to root */
  function createPanel() {
    if (document.getElementById(PANEL_ID)) return;

    const root = getOrCreateRoot();
    const panel = document.createElement('div');
    panel.id = PANEL_ID;
    panel.className = 'sop-panel';

    const header = document.createElement('div');
    header.className = 'sop-panel-header';
    header.innerHTML = '<span class="sop-panel-title">SOP Copilot</span>';
    const closeBtn = document.createElement('button');
    closeBtn.className = 'sop-panel-close';
    closeBtn.innerHTML = '&times;';
    closeBtn.setAttribute('aria-label', 'Close');
    closeBtn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      togglePanel();
    }, true);
    header.appendChild(closeBtn);

    const messages = document.createElement('div');
    messages.className = 'sop-messages';

    const inputArea = document.createElement('div');
    inputArea.className = 'sop-input-area';
    const inputRow = document.createElement('div');
    inputRow.className = 'sop-input-row';
    const input = document.createElement('textarea');
    input.className = 'sop-input';
    input.placeholder = 'Ask a policy or SOP question...';
    input.rows = 2;
    const sendBtn = document.createElement('button');
    sendBtn.className = 'sop-send-btn';
    sendBtn.textContent = 'Send';
    const includeSel = document.createElement('button');
    includeSel.className = 'sop-include-selection';
    includeSel.type = 'button';
    includeSel.textContent = 'Include selected text in question';

    inputRow.appendChild(input);
    inputRow.appendChild(sendBtn);
    inputArea.appendChild(inputRow);
    inputArea.appendChild(includeSel);

    panel.appendChild(header);
    panel.appendChild(messages);
    panel.appendChild(inputArea);
    root.appendChild(panel);

    // Send on button click
    sendBtn.addEventListener('click', () => sendMessage(input, messages, sendBtn));
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage(input, messages, sendBtn);
      }
    });

    // Include selected text in input (append or prefill)
    includeSel.addEventListener('click', () => {
      const text = getSelectedText();
      if (text) {
        const current = input.value.trim();
        input.value = current ? current + '\n\n--- Selected text ---\n\n' + text : text;
        input.focus();
      }
    });

    // Draggable panel: drag header to move
    let dragStartX, dragStartY, panelStartLeft, panelStartTop;
    header.addEventListener('mousedown', (e) => {
      if (e.target.closest('.sop-panel-close')) return;
      const rect = panel.getBoundingClientRect();
      dragStartX = e.clientX;
      dragStartY = e.clientY;
      panelStartLeft = rect.left;
      panelStartTop = rect.top;
      panel.style.right = 'auto';
      panel.style.left = panelStartLeft + 'px';
      panel.style.top = panelStartTop + 'px';
      panel.style.width = rect.width + 'px';
      panel.style.height = rect.height + 'px';

      function onMouseMove(e) {
        const dx = e.clientX - dragStartX;
        const dy = e.clientY - dragStartY;
        panel.style.left = (panelStartLeft + dx) + 'px';
        panel.style.top = Math.max(0, panelStartTop + dy) + 'px';
      }
      function onMouseUp() {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
      }
      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
    });

    // When panel opens, optionally prefill with selected text
    const observer = new MutationObserver(() => {
      if (panel.classList.contains('open')) {
        const sel = getSelectedText();
        if (sel && !input.value.trim()) {
          input.placeholder = 'Question (selected text will be included if you click "Include selected text")';
        }
      }
    });
    observer.observe(panel, { attributes: true, attributeFilter: ['class'] });
  }

  function togglePanel() {
    createPanel();
    const panel = document.getElementById(PANEL_ID);
    if (panel) {
      panel.classList.toggle('open');
      console.log('SOP Copilot: panel toggled', panel.classList.contains('open') ? 'open' : 'closed');
    }
  }

  /** Append a message div to the messages container */
  function addMessage(messagesEl, role, content, isError) {
    const div = document.createElement('div');
    div.className = 'sop-msg ' + (isError ? 'error' : role);
    const label = role === 'user' ? 'You' : 'SOP Copilot';
    div.innerHTML = '<span class="sop-msg-label">' + escapeHtml(label) + '</span>' + escapeHtml(content).replace(/\n/g, '<br>');
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
  }

  /** Send message via background; include page context when available for web-grounded answers. */
  function sendMessage(inputEl, messagesEl, sendBtn) {
    const question = (inputEl.value || '').trim();
    if (!question) return;

    inputEl.value = '';
    addMessage(messagesEl, 'user', question, false);

    const typingEl = document.createElement('div');
    typingEl.className = 'sop-typing';
    typingEl.innerHTML = '<span></span><span></span><span></span>';
    messagesEl.appendChild(typingEl);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    sendBtn.disabled = true;

    const pageContent = extractPageContent();
    const message = pageContent && pageContent.length > 20
      ? PAGE_CTX_MARKER + '\n' + pageContent + '\n' + USER_Q_MARKER + '\n' + question
      : question;

    chrome.runtime.sendMessage({ action: 'chat', message: message }, (response) => {
      typingEl.remove();
      sendBtn.disabled = false;
      if (chrome.runtime.lastError) {
        addMessage(messagesEl, 'assistant', 'Extension error. Try reloading the extension.', true);
        console.error('SOP Copilot:', chrome.runtime.lastError);
        return;
      }
      const ok = response && response.ok;
      const data = response && response.data;
      const reply = data && typeof data.reply === 'string' ? data.reply.trim() : '';
      if (ok && reply) {
        addMessage(messagesEl, 'assistant', reply, false);
      } else {
        const errMsg = reply || (data && data.detail) || (data && data.error) || 'Backend error. Ensure server is running at ' + API_BASE + '.';
        addMessage(messagesEl, 'assistant', errMsg, true);
      }
    });
  }

  function init() {
    if (!document.body) {
      document.addEventListener('DOMContentLoaded', init);
      return;
    }
    createFab();
    createPanel();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    setTimeout(init, 0);
  }

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg && msg.action === 'togglePanel') {
      console.log('SOP Copilot: received togglePanel from popup/background');
      togglePanel();
      sendResponse({ ok: true });
    }
    return true;
  });
})();
