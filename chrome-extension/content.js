const SIDEBAR_ID = 'sop-copilot-sidebar';
const SIDEBAR_WIDTH = 420;

function createSidebar() {
  if (document.getElementById(SIDEBAR_ID)) return;

  const sidebar = document.createElement('div');
  sidebar.id = SIDEBAR_ID;
  sidebar.className = 'sop-copilot-sidebar';
  sidebar.innerHTML = `
    <div class="sop-copilot-header">
      <span>📋 SOP Copilot</span>
      <button id="sop-close-btn" title="Close">×</button>
    </div>
    <div class="sop-copilot-body">
      <iframe src="http://localhost:5174" class="sop-iframe"></iframe>
    </div>
  `;

  document.body.appendChild(sidebar);

  document.getElementById('sop-close-btn').addEventListener('click', () => {
    sidebar.classList.remove('open');
  });
}

function toggleSidebar() {
  let sidebar = document.getElementById(SIDEBAR_ID);
  if (!sidebar) {
    createSidebar();
    sidebar = document.getElementById(SIDEBAR_ID);
  }
  sidebar.classList.toggle('open');
}

chrome.runtime.onMessage.addListener((msg, _sender, _sendResponse) => {
  if (msg.action === 'toggleSidebar') toggleSidebar();
});
