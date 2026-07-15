# Multi-Agent AI Customer Support Assistant (RAG + LLMs)

A working implementation of the capstone project spec: a multi-agent customer
support system with intent detection, agent routing, RAG over a company
knowledge base, conversation memory, and escalation/ticketing.

## What's included

```
customer-support-ai/
├── backend/
│   ├── main.py              # FastAPI app: /auth/register, /auth/login, /chat, /history
│   ├── auth.py               # JWT auth + password hashing
│   ├── llm.py                 # LLM wrapper (OpenAI-compatible; has offline MOCK_MODE)
│   ├── database/db.py         # SQLite: users, conversation memory, tickets
│   ├── agents/
│   │   ├── intent_detection.py  # Module 3: classifies query into billing/technical/product/complaint/faq
│   │   ├── router.py            # Module 4: routes to 1+ agents, aggregates responses
│   │   ├── base.py              # shared retrieve-then-generate logic
│   │   ├── billing.py           # Module 5
│   │   ├── technical.py
│   │   ├── product.py
│   │   ├── complaint.py         # also creates escalation tickets
│   │   └── faq.py
│   ├── rag/
│   │   ├── ingest.py          # Module 7: chunk -> embed -> store in FAISS
│   │   └── retriever.py        # semantic search over the FAISS index
│   ├── requirements.txt
│   └── .env.example
├── knowledge_base/            # Module 6: sample TechMart Electronics documents
│   ├── faq.txt
│   ├── refund_policy.txt
│   ├── shipping_policy.txt
│   ├── warranty.txt
│   └── pricing.txt
├── frontend/
│   └── index.html             # single-file chat UI (login/register, chat, typing indicator)
└── README.md
```

This matches the architecture in the project brief:
`Web Chat -> Backend API -> Intent Detection -> Agent Router -> [Billing/Technical/Product/Complaint/FAQ Agents] -> RAG Retrieval -> Response Aggregator -> Final Response`,
with Conversation Memory running alongside.

## How it works

1. **Intent Detection** (`agents/intent_detection.py`) — fast keyword-based
   classifier that can tag a query with one or more intents (e.g. "I paid
   yesterday but Premium is still locked" → `["billing", "technical"]`).
   Swap this for an LLM-based classifier any time by calling `llm.chat_completion()`
   with a classification prompt instead.
2. **Agent Router** (`agents/router.py`) — looks up the matching agent(s) for
   each detected intent and invokes them.
3. **Each agent** (`agents/billing.py`, etc.) retrieves relevant chunks from
   the FAISS vector store (`rag/retriever.py`), builds a prompt with that
   context, and calls the LLM (`llm.py`).
4. **Response Aggregator** (in `router.py`) combines multiple agent replies
   into one labeled response when more than one agent was invoked.
5. **Conversation Memory** (`database/db.py`) stores every message per
   session and feeds recent history back into the next request.
6. **Escalation**: the Complaint Agent flags `escalate: true`; the backend
   then creates a ticket row so it can be picked up by a human agent.

## Setup — step by step

### 1. Prerequisites
- Python 3.11+
- (Optional) An OpenAI API key — or a key for any OpenAI-compatible provider
  (Groq for Llama 3, etc.). **Without a key, the system runs in MOCK_MODE**
  so you can test the whole pipeline for free before wiring up a real LLM.

### 2. Install backend dependencies
```bash
cd customer-support-ai/backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# open .env and paste your OPENAI_API_KEY if you have one
# (leave MOCK_MODE=auto to run without a key)
```

### 4. Build the RAG vector index
This reads everything in `knowledge_base/`, chunks it, embeds it with
`sentence-transformers/all-MiniLM-L6-v2`, and saves a FAISS index.
```bash
cd backend
python -m rag.ingest
```
Re-run this any time you add/edit files in `knowledge_base/`.

### 5. Run the backend
```bash
uvicorn main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` for interactive Swagger API docs.

### 6. Run the frontend
The frontend is a single static HTML file — no build step needed.
```bash
# from customer-support-ai/frontend
python -m http.server 5500
```
Open `http://localhost:5500/index.html` in your browser. Register a user,
log in, and start chatting.

> If you deploy the backend somewhere other than `localhost:8000`, update
> `const API_BASE = "..."` near the top of `frontend/index.html`'s `<script>`.

### 7. Try a multi-agent routing example
Ask: *"I paid yesterday but Premium is still locked."*
This should trigger **both** the Billing Agent and Technical Agent, and
you'll see `Agent(s): billing, technical` under the reply.

## Turning on a real LLM
Set in `.env`:
```
OPENAI_API_KEY=sk-...
MOCK_MODE=false
LLM_MODEL=gpt-4o-mini
```
To use Groq (fast, free-tier Llama 3) or another OpenAI-compatible provider
instead, add a `base_url` to the `OpenAI(...)` client construction in
`backend/llm.py::_get_client()`.

## Next steps to finish the project for submission

1. **Expand the knowledge base** — the 5 sample `.txt` files cover the
   basics; add real PDFs (`UserManual.pdf`, `InstallationGuide.pdf`,
   `Products.pdf`) for a richer demo, then re-run `python -m rag.ingest`
   (PDF ingestion is already supported).
2. **Wire up a real LLM key** and test the quality of answers end-to-end,
   tuning each agent's `system_prompt` in `agents/*.py` as needed.
3. **Swap SQLite for MongoDB/PostgreSQL** if your evaluation requires it —
   only `database/db.py` needs to change; every other file calls its
   functions, not the database directly.
4. **Build out the React/Next.js frontend** (optional, since the included
   HTML/JS frontend is fully functional) if your rubric specifically
   requires React — the API surface (`/auth/register`, `/auth/login`,
   `/chat`, `/history/{session_id}`) stays identical either way.
5. **Deploy**:
   - Backend → Railway or Render (add `Procfile`: `web: uvicorn main:app --host 0.0.0.0 --port $PORT`)
   - Frontend → Vercel (or just serve the static file from the same host)
   - Swap SQLite for MongoDB Atlas if going to production
6. **Add the analytics dashboard** (Module 9, optional/bonus) — you already
   have everything you need in the `conversations` and `tickets` tables to
   build simple count/aggregation queries.
7. **Record your demo video** showing: login → a billing question → a
   technical question → a multi-agent question → an escalation/complaint
   creating a ticket → conversation history persisting across messages.
8. **Write your project report** using this README + the architecture
   diagram from the brief as your basis.

## Notes on what's simplified vs. the full brief
- Intent detection here is keyword-based for speed/determinism and zero
  API cost; the brief allows either approach — mention which one you used
  in your report and why.
- The frontend is plain HTML/JS rather than a full Next.js app, since the
  API contract is the same either way — this keeps setup to zero build
  steps. Migrating it into a Next.js page is straightforward if your
  rubric requires React specifically (Frontend Design is only 10/100 marks).
- Analytics dashboard (Module 9) and voice/multilingual bonuses are left
  as extensions per the brief's "Optional"/"Bonus" labeling.
