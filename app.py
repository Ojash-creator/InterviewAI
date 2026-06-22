"""
InterviewAI — Flask Backend (100% FREE VERSION)
AI: Google Gemini 1.5 Flash (free tier — 15 req/min, 1500 req/day)
DB: SQLite (local) / PostgreSQL (Render free tier)
Get free API key: https://aistudio.google.com/app/apikey
"""

import os, json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
app.config.update(
    SQLALCHEMY_DATABASE_URI       = os.getenv("DATABASE_URL", "sqlite:///interviewai.db"),
    SQLALCHEMY_TRACK_MODIFICATIONS= False,
    JWT_SECRET_KEY                = os.getenv("JWT_SECRET", "dev-secret-change-in-prod"),
    JWT_ACCESS_TOKEN_EXPIRES      = timedelta(days=7),
)

CORS(app, origins=os.getenv("FRONTEND_URL", "*").split(","))
db      = SQLAlchemy(app)
bcrypt  = Bcrypt(app)
jwt     = JWTManager(app)

# ── Gemini Setup (FREE) ───────────────────────────────────────────────────────
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
gemini = genai.GenerativeModel("gemini-1.5-flash")   # Free model


def ask_gemini(prompt: str, system: str = "") -> str:
    """Call Gemini free API with fallback."""
    try:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = gemini.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        app.logger.warning(f"Gemini error: {e}")
        raise


# ── Models ────────────────────────────────────────────────────────────────────
class User(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    sessions      = db.relationship("Session", backref="user", lazy=True,
                                    cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email}


class Session(db.Model):
    id                 = db.Column(db.Integer, primary_key=True)
    user_id            = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role               = db.Column(db.String(100))
    category           = db.Column(db.String(50))
    difficulty         = db.Column(db.String(50))
    overall_score      = db.Column(db.Float, default=0)
    questions_answered = db.Column(db.Integer, default=0)
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)
    answers            = db.relationship("Answer", backref="session", lazy=True,
                                         cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, "role": self.role, "category": self.category,
            "difficulty": self.difficulty,
            "overall_score": round(self.overall_score, 1),
            "questions_answered": self.questions_answered,
            "created_at": self.created_at.isoformat(),
        }


class Answer(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    session_id    = db.Column(db.Integer, db.ForeignKey("session.id"), nullable=False)
    question      = db.Column(db.Text)
    answer_text   = db.Column(db.Text)
    score         = db.Column(db.Float, default=0)
    communication = db.Column(db.Float, default=0)
    clarity       = db.Column(db.Float, default=0)
    relevance     = db.Column(db.Float, default=0)
    structure     = db.Column(db.Float, default=0)
    feedback      = db.Column(db.Text)
    strength      = db.Column(db.String(200))
    improve       = db.Column(db.String(200))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "question": self.question,
            "score": self.score, "communication": self.communication,
            "clarity": self.clarity, "relevance": self.relevance,
            "structure": self.structure, "feedback": self.feedback,
            "strength": self.strength, "improve": self.improve,
        }


# ── Helpers ───────────────────────────────────────────────────────────────────
def uid():    return int(get_jwt_identity())
def err(m, c=400): return jsonify({"error": m}), c
def ok(d, c=200):  return jsonify(d), c


# ── Auth ──────────────────────────────────────────────────────────────────────
@app.route("/api/auth/register", methods=["POST"])
def register():
    d        = request.get_json() or {}
    name     = (d.get("name") or "").strip()
    email    = (d.get("email") or "").strip().lower()
    password = d.get("password") or ""

    if not all([name, email, password]):
        return err("All fields are required")
    if len(password) < 8:
        return err("Password must be at least 8 characters")
    if User.query.filter_by(email=email).first():
        return err("Email already registered", 409)

    user = User(
        name=name, email=email,
        password_hash=bcrypt.generate_password_hash(password).decode()
    )
    db.session.add(user)
    db.session.commit()
    token = create_access_token(identity=str(user.id))
    return ok({"token": token, "user": user.to_dict()}, 201)


@app.route("/api/auth/login", methods=["POST"])
def login():
    d        = request.get_json() or {}
    email    = (d.get("email") or "").strip().lower()
    password = d.get("password") or ""
    user     = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return err("Invalid email or password", 401)
    token = create_access_token(identity=str(user.id))
    return ok({"token": token, "user": user.to_dict()})


@app.route("/api/auth/me")
@jwt_required()
def me():
    user = User.query.get(uid())
    return ok(user.to_dict()) if user else err("Not found", 404)


# ── Sessions ──────────────────────────────────────────────────────────────────
@app.route("/api/sessions", methods=["POST"])
@jwt_required()
def create_session():
    d = request.get_json() or {}
    s = Session(user_id=uid(), role=d.get("role"),
                category=d.get("category"), difficulty=d.get("difficulty"))
    db.session.add(s); db.session.commit()
    return ok(s.to_dict(), 201)


@app.route("/api/sessions")
@jwt_required()
def list_sessions():
    rows = Session.query.filter_by(user_id=uid())\
               .order_by(Session.created_at.desc()).limit(20).all()
    return ok([r.to_dict() for r in rows])


@app.route("/api/sessions/<int:sid>", methods=["PUT"])
@jwt_required()
def update_session(sid):
    s = Session.query.filter_by(id=sid, user_id=uid()).first()
    if not s: return err("Not found", 404)
    d = request.get_json() or {}
    if "overall_score"      in d: s.overall_score      = float(d["overall_score"])
    if "questions_answered" in d: s.questions_answered = int(d["questions_answered"])
    db.session.commit()
    return ok(s.to_dict())


# ── AI: Feedback (Gemini FREE) ────────────────────────────────────────────────
@app.route("/api/ai/feedback", methods=["POST"])
@jwt_required()
def ai_feedback():
    d          = request.get_json() or {}
    question   = (d.get("question") or "").strip()
    answer     = (d.get("answer")   or "").strip()
    session_id = d.get("session_id")

    if not question or not answer:
        return err("question and answer are required")

    SYSTEM = """You are an expert interview coach. Evaluate the candidate's answer strictly.
Return ONLY a valid JSON object — no markdown, no backticks, no extra text:
{"score":75,"communication":70,"clarity":80,"relevance":72,"structure":68,
"feedback":"2-3 sentence specific coaching advice here.",
"strength":"one short phrase","improve":"one short phrase"}
All scores must be integers 0-100."""

    PROMPT = f"Interview Question: {question}\n\nCandidate Answer: {answer}"

    try:
        raw = ask_gemini(PROMPT, SYSTEM)
        # Strip any accidental markdown fences
        raw = raw.replace("```json", "").replace("```", "").strip()
        # Extract JSON if wrapped in extra text
        start, end = raw.find("{"), raw.rfind("}") + 1
        if start >= 0 and end > start:
            raw = raw[start:end]
        fb = json.loads(raw)
    except Exception as e:
        app.logger.warning(f"Gemini feedback fallback triggered: {e}")
        fb = {
            "score": 70, "communication": 70, "clarity": 72,
            "relevance": 68, "structure": 70,
            "feedback": "Good attempt! Strengthen your answer by quantifying results and using the STAR method (Situation, Task, Action, Result) to add clear structure.",
            "strength": "Clear delivery", "improve": "Add measurable outcomes"
        }

    # Persist to DB
    if session_id:
        try:
            rec = Answer(
                session_id=session_id, question=question, answer_text=answer,
                score=fb.get("score", 70), communication=fb.get("communication", 70),
                clarity=fb.get("clarity", 70), relevance=fb.get("relevance", 70),
                structure=fb.get("structure", 70), feedback=fb.get("feedback", ""),
                strength=fb.get("strength", ""), improve=fb.get("improve", ""),
            )
            db.session.add(rec); db.session.commit()
        except Exception as e:
            app.logger.warning(f"Answer save error: {e}")

    return ok(fb)


# ── AI: Chat Coach (Gemini FREE) ──────────────────────────────────────────────
@app.route("/api/ai/chat", methods=["POST"])
@jwt_required()
def ai_chat():
    d       = request.get_json() or {}
    message = (d.get("message") or "").strip()
    history = d.get("history") or []

    if not message: return err("message is required")

    SYSTEM = ("You are a warm, expert interview coach helping candidates land their dream jobs. "
              "Give concise, practical, actionable advice in under 100 words. "
              "Write in natural conversational prose — no bullet points.")

    # Build conversation context
    ctx = ""
    for m in history[-6:]:
        role = "User" if m.get("role") == "user" else "Coach"
        ctx += f"{role}: {m.get('content','')}\n"
    ctx += f"User: {message}"

    try:
        reply = ask_gemini(ctx, SYSTEM)
    except Exception:
        reply = ("Great question! Always use the STAR method for behavioural answers — "
                 "Situation, Task, Action, Result — and quantify your impact wherever possible.")

    return ok({"reply": reply})


# ── Stats ─────────────────────────────────────────────────────────────────────
@app.route("/api/stats")
@jwt_required()
def stats():
    sessions = Session.query.filter_by(user_id=uid()).all()
    scores   = [s.overall_score for s in sessions if s.overall_score > 0]
    return ok({
        "sessions"  : len(sessions),
        "avg_score" : round(sum(scores) / len(scores), 1) if scores else 0,
        "questions" : sum(s.questions_answered for s in sessions),
        "best_score": round(max(scores), 1) if scores else 0,
    })


# ── Health ────────────────────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    return ok({"status": "ok", "version": "2.0-free", "ai": "gemini-1.5-flash"})


# ── Startup ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Seed demo user
        if not User.query.filter_by(email="demo@interviewai.app").first():
            demo = User(
                name="Demo User", email="demo@interviewai.app",
                password_hash=bcrypt.generate_password_hash("demo1234").decode()
            )
            db.session.add(demo); db.session.commit()
            print("✓ Demo user: demo@interviewai.app / demo1234")
    print("✓ DB ready  →  http://localhost:5000")
    app.run(debug=True, port=5000)
