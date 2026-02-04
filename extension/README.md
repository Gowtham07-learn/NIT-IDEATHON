# SOP Copilot – Browser Extension (Manifest V3)

Policy & SOP assistant on any website. Sider-style slide-in chat; uses `POST http://localhost:8000/chat`.

## Load in Chrome/Edge

1. Start the backend: `cd backend && uvicorn main:app --port 8000`
2. Open `chrome://extensions` (or `edge://extensions`)
3. Enable **Developer mode**
4. Click **Load unpacked** and select this `extension/` folder

## Usage

- **Floating button:** Bottom-right on every page; click to open/close the chat panel
- **Popup:** Click the extension icon → "Open chat panel" toggles the panel on the current tab
- **Selected text:** Select text on the page, then click "Include selected text in question" to append it to your message
- **Send:** Type a question and press Enter or click Send. Requests go to `POST http://localhost:8000/chat` with `{ "message": "string" }`

## Files

| File | Role |
|------|------|
| `manifest.json` | Manifest V3; permissions, content_scripts, background, popup |
| `content.js` | Injects FAB + panel; POST /chat; selected-text; draggable header |
| `background.js` | Service worker; relays popup → content script |
| `styles.css` | Floating button + slide-in panel + chat UI |
| `popup.html` / `popup.js` | Popup UI and "Open chat panel" action |
| `create_icons.py` | Run once to generate `icons/icon16.png`, etc. |

## Icons

If icons are missing, run from `extension/`:

```bash
python create_icons.py
```

Then reload the extension.
