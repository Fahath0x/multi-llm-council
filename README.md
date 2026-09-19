# Multi LLM Council

![LLM Council](header.jpg)

> **Multi-model deliberation with blind peer review.** Ask once, get a structured verdict from a panel of LLMs that anonymously rank each other — then a Chairman synthesizes the final answer.

---

## How It Works

A query goes through three sequential stages, all streamed live:

```
User Query
    │
    ▼
┌─────────────────────────────────────────┐
│  Stage 1 — Parallel Independent Opinions│  ← All council models answer in parallel
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│  Stage 2 — Blind Peer Review & Ranking  │  ← Responses anonymised (A, B, C...)
│  Kendall's W consensus score computed   │  ← Each model ranks the others
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│  Stage 3 — Chairman Synthesis           │  ← One model writes the final verdict
└─────────────────────────────────────────┘
```

**Why blind review?** Models receive `Response A / B / C` labels — no model IDs — so they can't self-promote or defer to a famous name. The de-anonymisation happens client-side purely for display.

---

## Deliberation Modes (Personas)

Switch the analytical framework per query:

| Persona | Focus |
|---|---|
| ⚖️ **Strict Truth & Logic** | Zero sycophancy, error debunking, mathematical rigour |
| 🛡️ **Security & Red Team** | OWASP Top 10, exploit vectors, hardened remediation |
| 💻 **Principal Architect** | Big-O, system design, scalability trade-offs |
| 🔬 **Scientific & Math Rigor** | Formal proofs, first-principles derivation |
| 🚀 **Startup & Product Strategy** | PMF, unit economics, GTM moat |
| 🧑‍⚖️ **Devil's Advocate** | Contrarian stress-tests, failure modes, blind spots |

---

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.10+, FastAPI, async httpx, SSE streaming |
| Frontend | React 19, Vite 7, react-markdown |
| LLM API | [OpenRouter](https://openrouter.ai) — any model, one key |
| Storage | JSON flat-files (`data/conversations/`) |
| Packaging | `uv` (Python), `npm` (JS) |
| Tests | pytest, FastAPI TestClient — 50 offline unit tests |

---

## Setup

### 1. Clone & install

```bash
# Python deps
uv sync

# Frontend deps
cd frontend && npm install && cd ..
```

### 2. API key

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-...
```

Get one at [openrouter.ai](https://openrouter.ai). Free-tier models are supported.

### 3. Run

```bash
# Option A — one command
./start.sh

# Option B — two terminals
uv run python -m backend.main   # → http://localhost:8001
cd frontend && npm run dev      # → http://localhost:5173
```

### 4. Test

```bash
uv run pytest tests/ -v
```

---

## Configuration

Council models and chairman are configurable live via the UI **Settings** panel, or via `backend/config.py` as defaults:

```python
COUNCIL_MODELS = [
    "deepseek/deepseek-v4-flash-0731:free",
    "nvidia/nemotron-3.5-lightning:free",
    "liquid/lfm-2.5-2.6b:free",
    "nex-agi/nex-n2.5-pro:free",
]
CHAIRMAN_MODEL = "deepseek/deepseek-v4-flash-0731:free"
```

Any [OpenRouter model slug](https://openrouter.ai/models) works — free or paid.

---

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/api/models` | Curated model catalogue |
| `GET` | `/api/personas` | Available deliberation modes |
| `GET/POST` | `/api/settings` | Get / update active council config |
| `GET` | `/api/conversations` | List conversations |
| `POST` | `/api/conversations` | Create conversation |
| `POST` | `/api/conversations/{id}/message/stream` | Run council (SSE stream) |
| `DELETE` | `/api/conversations/{id}` | Delete conversation |
