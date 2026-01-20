# Model Scout — SOTA Radar (Phase 1)

<p align="center">
  <img src="https://img.shields.io/badge/Phase-1_Vertical_Slice-22c55e?style=for-the-badge" alt="Phase 1">
  <img src="https://img.shields.io/badge/Mino.ai-Powered-00d4aa?style=for-the-badge" alt="Mino.ai Powered">
  <img src="https://img.shields.io/badge/React-18-61dafb?style=for-the-badge&logo=react" alt="React 18">
  <img src="https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask" alt="Flask 3.0">
  <img src="https://img.shields.io/badge/TypeScript-5.0-3178c6?style=for-the-badge&logo=typescript" alt="TypeScript">
</p>

> **"Easy to understand, easy to navigate, and highly presentable"**  
> A unified dashboard that solves benchmark fragmentation for ML engineers.

---

## 🎯 Phase 1 Mission

Build a **working vertical slice** of Model Scout: SOTA Radar that:

- ✅ **Extracts real benchmark data** from 6 specialized sources
- ✅ **Normalizes data** into a single transparent schema
- ✅ **Visualizes model capability fingerprints** via radar charts
- ✅ **Allows side-by-side model comparison**
- ✅ **Streams live extraction logs** via SSE

---

## 📊 Phase 1 Benchmarks (STRICT SCOPE)

| Category | Benchmark | URL | Metrics |
|----------|-----------|-----|---------|
| **General** | HuggingFace Open LLM Leaderboard | huggingface.co | MMLU, ARC, HellaSwag, TruthfulQA, WinoGrande, GSM8K |
| **General** | LMSYS Chatbot Arena | lmarena.ai | Arena ELO, Win Rate |
| **Economics** | Vellum LLM Leaderboard | vellum.ai | Input/Output Price, Speed, Latency, Context Window |
| **Coding** | LiveCodeBench | livecodebench.github.io | Pass@1, HumanEval, MBPP |
| **Safety** | MASK (Scale.com) | scale.com/leaderboard/mask | Lying Rate, Manipulation Score |
| **Safety** | Vectara Hallucination | github.com/vectara | Hallucination Rate |

> ⚠️ **Do NOT add additional benchmarks** without explicit approval.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Radar Chart (Capability Fingerprint)** | 4-axis visualization: Logic, Coding, Economics, Safety |
| **Model Comparison** | Side-by-side analysis with delta calculations |
| **Live Terminal Feed** | Real-time SSE stream showing agent progress |
| **Parallel Extraction** | `ThreadPoolExecutor(max_workers=5)` for concurrent Mino agents |
| **Intelligent Caching** | SQLite WAL mode for efficient data persistence |
| **SSE Keepalive** | Heartbeat comments every 10 seconds to prevent timeouts |

---

## 🏗️ Architecture

```
┌─────────────────────┐         ┌─────────────────────┐
│   React Frontend    │◄───────►│   Vercel Edge       │
│   (Vite + TS)       │   SSE   │   (Serverless)      │
└────────┬────────────┘         └─────────────────────┘
         │
         │ REST + SSE Stream
         ▼
┌─────────────────────────────────────────────────────┐
│              Flask Orchestrator (Railway)           │
│         ThreadPoolExecutor (max_workers=5)          │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐         │
│  │HuggingFace│ │LMSYS Arena│ │LiveCodeBench│        │
│  └───────────┘ └───────────┘ └───────────┘         │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐         │
│  │   Vellum  │ │   MASK    │ │  Vectara  │         │
│  └───────────┘ └───────────┘ └───────────┘         │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              Mino.ai SSE Endpoint                   │
│         POST /v1/automation/run-sse                 │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Mino.ai API Key

### Frontend Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your MINO_API_KEY to .env

# Start server
python app.py
```

### Environment Variables

#### Frontend (`.env`)
```env
VITE_API_URL=http://localhost:5000
```

#### Backend (`backend/.env`)
```env
MINO_API_KEY=your_mino_api_key_here
PORT=5000
```

---

## 📡 API Reference

### `POST /api/search`
Search for a model across all Phase 1 benchmark sources.

**Request:**
```json
{
  "model_name": "GPT-4o",
  "sources": ["huggingface", "lmsys_arena", "livecodebench", "vellum", "mask", "vectara"]
}
```

**SSE Response Events:**
```json
{
  "status": "running" | "completed" | "failed",
  "benchmark": "HuggingFace Open LLM Leaderboard",
  "message": "Connecting to source...",
  "timestamp": "2026-01-20T15:56:23.000Z"
}
```

---

### `POST /api/compare`
Compare two models side-by-side.

**Request:**
```json
{
  "model_a": "GPT-4o",
  "model_b": "Claude 3.5 Sonnet",
  "sources": ["huggingface", "lmsys_arena", "livecodebench", "vellum", "mask", "vectara"]
}
```

---

### `GET /api/sources`
Get available benchmark sources (Phase 1 only).

---

### `GET /api/leaderboard`
Get aggregated cross-benchmark leaderboard.

---

## 🔄 Extraction Flow

1. **Request Received**: Frontend sends model name to `/api/search`
2. **Parallel Dispatch**: `ThreadPoolExecutor(max_workers=5)` spawns workers
3. **Mino Extraction**: Each worker calls Mino with:
   - Source URL
   - Extraction goal (source-specific prompt)
   - System prompt (exact extraction instructions)
4. **SSE Streaming**: Events streamed back with 10-second keepalive
5. **Normalization**: Raw scores normalized to 0-100 (higher always better)
6. **Caching**: Results saved to SQLite (WAL mode)
7. **Completion**: Final `complete` event sent

---

## 📐 Normalization Logic

All scores are normalized to **0-100** where **higher is always better**.

```python
# Standard percentage scores (0-100)
normalized = score  # Already in range

# ELO scores (1000-1500 range)
normalized = ((elo - 1000) / 500) * 100

# Lower-is-better metrics (hallucination_rate, lying_rate)
normalized = 100 - score  # Inverted
```

### Metric Inversion Rules
These metrics are inverted (lower raw score = higher normalized score):
- `hallucination_rate`
- `lying_rate`
- `manipulation_score`
- `deception_score`

---

## 🆔 Model Identifier Mapping

Raw model names from benchmarks are mapped to **canonical internal `model_id`**:

| Raw Name | Canonical ID |
|----------|--------------|
| `gpt-4o` | `openai/gpt-4o` |
| `claude-3.5-sonnet` | `anthropic/claude-3.5-sonnet` |
| `gemini-1.5-pro` | `google/gemini-1.5-pro` |
| `llama-3-70b-instruct` | `meta/llama-3-70b-instruct` |
| `deepseek-v2-chat` | `deepseek/deepseek-v2-chat` |

See `backend/config.py` → `MODEL_ID_MAPPING` for complete mapping.

---

## 📂 Project Structure

```
modelscout/
├── src/
│   ├── components/
│   │   ├── BenchmarkChart.tsx
│   │   ├── ComparisonResults.tsx
│   │   ├── CrossBenchmarkTable.tsx
│   │   ├── ExpertiseRadarChart.tsx    # 4-axis radar chart
│   │   ├── ModelComparisonSelector.tsx
│   │   ├── SourceStatusCard.tsx
│   │   ├── TerminalFeed.tsx           # Live SSE log viewer
│   │   └── TopModelsCard.tsx
│   ├── hooks/
│   │   ├── useModelComparison.ts
│   │   └── useLeaderboard.ts
│   ├── pages/
│   │   ├── Index.tsx                  # Model overview
│   │   └── Compare.tsx                # Side-by-side comparison
│   └── index.css
├── backend/
│   ├── app.py                         # Flask server + SSE keepalive
│   ├── workers.py                     # Mino workers + ThreadPoolExecutor
│   ├── database.py                    # SQLite WAL mode
│   └── config.py                      # Phase 1 benchmarks + normalization
└── docs/
    └── MODEL_SCOUT_QUALIFIED_SUBMISSION.md
```

---

## 🚢 Deployment

### Frontend (Vercel)
1. Connect GitHub repository to Vercel
2. Set `VITE_API_URL` to your Railway backend URL
3. Deploy

### Backend (Railway)
1. Connect GitHub repository to Railway
2. Set environment variables (`MINO_API_KEY`, `PORT`)
3. Deploy

---

## ⚠️ Known Limitations (Phase 1)

1. **No authentication** - Open access only
2. **No real-time updates** - Data is cached for 24 hours
3. **No time-series diffs** - Historical comparison not implemented
4. **Mock leaderboard** - `/api/leaderboard` returns sample data
5. **Limited model mapping** - Not all model name variants covered

---

## 🔒 Mino API Contract

Mino is a **stateless extraction worker**.

**Input:**
```json
{
  "url": "https://huggingface.co/spaces/...",
  "goal": "Search for model X and extract scores...",
  "systemPrompt": "You are an autonomous benchmark extraction agent..."
}
```

**Output (Success):**
```json
{
  "status": "success",
  "payload": {
    "benchmark": "HuggingFace Open LLM Leaderboard",
    "model": "GPT-4o",
    "metrics": { "mmlu": 88.7, "arc": 85.2 },
    "rank": 1,
    "source_url": "https://...",
    "timestamp_utc": "2026-01-20T15:56:23Z"
  },
  "error_code": null
}
```

**Output (Failure):**
```json
{
  "status": "failure",
  "payload": null,
  "error_code": "UNREADABLE_FORMAT" | "SITE_BLOCKED" | "LAYOUT_CHANGED"
}
```

---

## 📄 License

MIT © Tinyfish

---

<p align="center">
  <strong>Built with ❤️ by Tinyfish Solutions Engineering</strong>
</p>
