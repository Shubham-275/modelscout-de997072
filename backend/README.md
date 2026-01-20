# Model Scout Backend (Phase 1)

Flask-based orchestration layer for Model Scout: SOTA Radar.

## Phase 1 Scope

This backend implements a **working vertical slice** of the Model Scout system with:

- **6 Benchmark Sources** (General, Economics, Coding, Safety)
- **ThreadPoolExecutor(max_workers=5)** for parallel extraction
- **SQLite WAL mode** for efficient concurrent writes
- **SSE streaming** with 10-second keepalive comments
- **Mino API integration** for intelligent web extraction

## Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your MINO_API_KEY

# Start server
python app.py
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MINO_API_KEY` | Yes | - | Mino.ai API key for extraction |
| `PORT` | No | 5000 | Server port |
| `DATABASE_PATH` | No | `./modelscout.db` | SQLite database path |
| `FLASK_DEBUG` | No | `false` | Enable debug mode |

## API Endpoints

### `GET /health`
Health check for deployment.

### `GET /api/sources`
List available Phase 1 benchmark sources.

### `POST /api/search`
Search for a model across benchmarks.

**Request:**
```json
{
  "model_name": "GPT-4o",
  "sources": ["huggingface", "lmsys_arena", "livecodebench", "vellum", "mask", "vectara"]
}
```

**Response:** SSE stream with events:
```
data: {"status": "running", "benchmark": "HuggingFace", "message": "..."}

data: {"type": "result", "status": "completed", "data": {...}}

: keepalive 2026-01-20T15:56:23

data: {"type": "complete", "status": "completed", "message": "All sources processed"}
```

### `POST /api/compare`
Compare two models side-by-side.

### `GET /api/history/<model_name>`
Get historical benchmark data for a model.

### `GET /api/cached/<model_name>`
Get cached results for a model.

### `GET /api/leaderboard`
Get aggregated leaderboard (mock data for Phase 1).

## Architecture

```
app.py          # Flask server, SSE keepalive, routes
├── workers.py  # Mino workers, ThreadPoolExecutor
├── database.py # SQLite WAL mode, caching
└── config.py   # Phase 1 benchmarks, normalization rules
```

## Normalization Rules

All scores are normalized to **0-100** where **higher is always better**.

### Standard Scores (0-100%)
```python
normalized = raw_score  # Already in 0-100 range
```

### ELO Scores (1000-1500 range)
```python
normalized = ((elo - 1000) / 500) * 100
```

### Lower-is-Better Metrics
Inverted metrics (hallucination_rate, lying_rate, etc.):
```python
normalized = 100 - raw_score
```

## Mino API Contract

The backend uses Mino as a **stateless extraction worker**.

### Request
```json
{
  "url": "https://huggingface.co/spaces/...",
  "goal": "Search for model X...",
  "systemPrompt": "You are an autonomous benchmark extraction agent...",
  "browserProfile": "stealth"
}
```

### Extraction Prompt (Exact)
```
You are an autonomous benchmark extraction agent.

TASK:
Extract model performance data from the provided URL.

RULES:
- Extract ONLY what is explicitly present.
- Do NOT infer missing values.
- Do NOT normalize.
- Preserve metric names and units exactly.
- If a value is unavailable, return null.
- If extraction fails, return error_code.

OUTPUT:
Strict JSON following the provided schema.
```

### Response Contract
```json
{
  "status": "success" | "failure",
  "payload": {
    "benchmark": "string",
    "model": "string",
    "metrics": { "<metric_name>": "number | string | null" },
    "rank": "number | null",
    "source_url": "string",
    "timestamp_utc": "string"
  },
  "error_code": null | "UNREADABLE_FORMAT" | "SITE_BLOCKED" | "LAYOUT_CHANGED"
}
```

## Model Identifier Mapping

Raw model names are mapped to canonical IDs:

| Raw | Canonical |
|-----|-----------|
| `gpt-4o` | `openai/gpt-4o` |
| `claude-3.5-sonnet` | `anthropic/claude-3.5-sonnet` |
| `llama-3-70b-instruct` | `meta/llama-3-70b-instruct` |

See `config.py` → `MODEL_ID_MAPPING` for complete mapping.

## Database Schema

```sql
-- WAL mode enabled for concurrent writes
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

-- Benchmark results
CREATE TABLE benchmark_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    source TEXT NOT NULL,
    rank INTEGER,
    average_score REAL,
    benchmark_metrics TEXT,  -- JSON
    scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_name, source, scraped_at)
);

-- Comparison cache
CREATE TABLE comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_a TEXT NOT NULL,
    model_b TEXT NOT NULL,
    comparison_data TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);
```

## Known Limitations

1. **24-hour cache** - Results cached for 24 hours
2. **No real-time updates** - Requires manual refresh
3. **Mock leaderboard** - `/api/leaderboard` returns sample data
4. **Limited model mapping** - Not all model variants covered
