# ⚡ InterviewAI — 100% FREE AI Interview Preparation System

> Full-stack AI app using **Google Gemini (free tier)** — no credit card, no paid APIs, no cost!

---

## 💰 Cost Breakdown — Everything FREE

| Service | Free Tier | Limit |
|---|---|---|
| **Google Gemini API** | ✅ Free | 15 req/min, 1500 req/day |
| **Render** (backend hosting) | ✅ Free | Sleeps after 15min inactivity |
| **Render PostgreSQL** | ✅ Free | 1GB storage |
| **Vercel** (frontend hosting) | ✅ Free | Unlimited |
| **GitHub** | ✅ Free | Unlimited public repos |

**Total monthly cost: $0.00**

---

## 🔑 Get Your FREE Gemini API Key (2 minutes)

1. Go to **https://aistudio.google.com/app/apikey**
2. Sign in with your Google account
3. Click **"Create API key"**
4. Copy the key — paste it in your `.env` file

That's it! No billing info, no credit card required.

---

## 🚀 Run Locally

### Terminal 1 — Backend
```bash
cd interviewai-free/backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Open .env → paste GEMINI_API_KEY=your_key_here
python app.py
# ✓ http://localhost:5000
# ✓ Demo user: demo@interviewai.app / demo1234
```

### Terminal 2 — Frontend
```bash
cd interviewai-free/frontend
npm install
cp .env.example .env
npm run dev
# ✓ http://localhost:3000
```

---

## 🌐 Deploy FREE Online

### Backend → Render (free)
1. render.com → New Web Service → connect GitHub
2. Root dir: `backend`
3. Add env var: `GEMINI_API_KEY` = your key
4. Add free PostgreSQL database
5. Deploy → get `.onrender.com` URL

### Frontend → Vercel (free)
1. vercel.com → New Project → import repo
2. Root dir: `frontend`
3. Add env var: `VITE_API_URL` = your Render URL
4. Deploy → get `.vercel.app` URL

---

## 📁 Project Structure
```
interviewai-free/
├── backend/
│   ├── app.py              ← Flask + Gemini AI
│   ├── requirements.txt
│   ├── Procfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── main.jsx
│   │   ├── context/AuthContext.jsx
│   │   ├── pages/
│   │   │   ├── AuthScreen.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Practice.jsx
│   │   │   └── Pages.jsx (History, Resources, Tips)
│   │   └── components/Layout.jsx (Topbar, Sidebar)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── vercel.json
├── render.yaml
└── .gitignore
```

---

## 💼 LinkedIn Post Template
```
🚀 Built InterviewAI — a FREE AI-powered Interview Prep System!

🤖 Uses Google Gemini AI (free tier) for:
• Real-time answer scoring across 4 metrics
• Personalised coaching chat
• 6 job roles, 4 question categories

🛠 Stack: React 18 + Flask + SQLite/PostgreSQL + Gemini AI
💰 Cost: $0/month — 100% free to build and deploy!

🔗 Live: [YOUR_VERCEL_URL]
💻 GitHub: [YOUR_GITHUB_URL]

#AI #FullStack #Free #Gemini #React #Python #Flask
```
