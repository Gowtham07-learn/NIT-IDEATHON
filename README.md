Commands to Run the UI
Fix: "Backend unreachable"
If the chatbot shows Backend unreachable, start the API server first:

cd backend
pip install -r requirements.txt
uvicorn main:app --port 8000
Leave that terminal open. Then open the chatbot (http://localhost:5174) or use the extension. Optional: create backend/.env with GROQ_API_KEY=your_key for live AI (see https://console.groq.com).

Prerequisites
Python 3.10+
Node.js 18+
Internet access
Option A: React Chatbot UI (SOP Copilot)
Required: Create backend/.env with GROQ_API_KEY=your_key (from https://console.groq.com). Do not hardcode.

Terminal 1 – Backend API
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
Verify: http://localhost:8000/docs must show GET /health and POST /chat.

Terminal 2 – Chatbot UI
cd chatbot-ui
npm install
npm run dev
Open: http://localhost:5174 — typing "What is SOP?" should return a structured SOP answer.

Option B: DPI Streamlit Dashboard
Terminal 1 – Monitor (collects data)
python monitor.py
Terminal 2 – Streamlit App
pip install -r requirements.txt
streamlit run app.py
Open: http://localhost:8501

Option C: Run All (Full Stack)
Terminal 1 – Monitor
python monitor.py
Terminal 2 – Backend API
cd backend
pip install -r requirements.txt
uvicorn main:app --port 8000
Terminal 3 – Chatbot UI
cd chatbot-ui
npm install
npm run dev
Terminal 4 – Streamlit Dashboard
streamlit run app.py
URLs:

Chatbot: http://localhost:5174
Dashboard: http://localhost:8501
Quick One-Liners (from project root)
# Chatbot only (backend must be running separately)
cd chatbot-ui && npm install && npm run dev

# Streamlit only (monitor recommended in another terminal)
streamlit run app.py

# Backend only
cd backend && uvicorn main:app --port 8000
