# Campus Customs — HW4

A Yale-merchandise storefront with an AI shopping assistant.

- **Frontend** — React + Vite + TypeScript (`frontend/`)
- **Backend** — FastAPI + Pydantic AI (`backend/`), model calls routed through
  the **Portkey** gateway
- **Agent** — four files under `backend/`: `prompts/prompt.md` (system prompt),
  `agent.py` (entry/wiring), `tools.py` (tools it can call), `models.py`
  (Pydantic types)

## 1. Place the data pack

The dataset is **not** in this repository. Put it at the repo root so the paths
are:

```
data/
├── campus_customs.db
└── products/          # product images referenced by the catalogue
```

## 2. Configure the API key

The key is read from the environment and is never committed. Copy the example
and add your Portkey key:

```bash
cp .env.example .env
# then edit .env and set API_PORTKEY_API_KEY
```

(`.env` at the repo root or at `backend/.env` both work; a real environment
variable takes precedence.)

## 3. Run the backend

Python 3.11+.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

Set `CHAT_MODE=stub` to run the chat offline (canned reply, no model call).

## 4. Run the frontend

Node 18+.

```bash
cd frontend
npm install
npm run dev
```

Opens http://localhost:5173. The Vite dev server proxies `/api` and `/images`
to the backend on port 8000, so start the backend first.

## Try it

- Browse **Products**, filter/search, open a product, use the **size finder**.
- Open the chat (bottom-right) and ask *"what hoodies do you have?"* (updates the
  page) or *"is the baseball crewneck in stock in XL?"* (reads live stock).
- A seeded test account is available: `test@campuscustoms.yale.edu` / `password`.
  Signed-in shoppers' chat history is saved and reloaded.

## Project docs

- `output/harness.md` — full system reference (DB, tools, safety, specs)
- `output/design.md` — design system
- `output/usability.md` — usability improvements
- `output/app_check.html` — live-site checks with screenshots
- `output/audit_trail.json` — append-only log of agent activity
- `AI_prompts.md` — the prompt log for the assignment
