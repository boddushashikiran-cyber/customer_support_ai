"""
Multi-Agent AI Customer Support Assistant - Backend API

Run with:
    uvicorn main:app --reload --port 8000

Docs available at http://localhost:8000/docs
"""
import uuid
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db
from auth import register_user, authenticate_user, get_current_user
from agents.router import route_query

app = FastAPI(title="Multi-Agent AI Customer Support Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    db.init_db()


# ---------- Schemas ----------

class AuthRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


# ---------- Auth endpoints (Module 1) ----------

@app.post("/auth/register")
def register(payload: AuthRequest):
    token = register_user(payload.username, payload.password)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/auth/login")
def login(payload: AuthRequest):
    token = authenticate_user(payload.username, payload.password)
    return {"access_token": token, "token_type": "bearer"}


# ---------- Chat endpoint (Modules 2-8) ----------

@app.post("/chat")
def chat(payload: ChatRequest, username: str = Depends(get_current_user)):
    session_id = payload.session_id or str(uuid.uuid4())

    # Pull recent conversation memory (Module 8) for context
    past = db.get_history(session_id, limit=10)
    history = [{"role": m["role"], "content": m["content"]} for m in past]

    db.save_message(session_id, username, "user", payload.message)

    result = route_query(payload.message, history=history)

    db.save_message(
        session_id, username, "assistant",
        result["final_response"], agent=",".join(result["agents_invoked"]),
    )

    if result["escalated"]:
        ticket_id = db.create_ticket(session_id, username, payload.message)
        result["ticket_id"] = ticket_id

    result["session_id"] = session_id
    return result


@app.get("/history/{session_id}")
def history(session_id: str, username: str = Depends(get_current_user)):
    return db.get_history(session_id, limit=100)


@app.get("/")
def root():
    return {"status": "ok", "service": "Multi-Agent AI Customer Support Assistant"}
