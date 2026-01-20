# Model Scout: SOTA Radar - Phase 1 Submission

## Project Status: ✅ Phase 1 Complete (Vertical Slice)

This submission fully implements the Phase 1 requirements for Model Scout, a unified dashboard for AI model benchmarks.

### Core Components Implemented

#### 1. Backend Infrastructure (Flask + Mino)
- **Orchestrator**: Flask server managing parallel extraction via `ThreadPoolExecutor(max_workers=5)`.
- **Extraction**: `workers.py` integrates with Mino.ai API to "snipe" benchmark data.
- **Streaming**: Implemented robust SSE (Server-Sent Events) with **10-second keepalive** comments.
- **Persistence**: SQLite database configured with `WAL` mode for high-concurrency writes.
- **Configuration**: Strict enforcement of the 6 Phase 1 benchmark sources.

#### 2. Frontend Dashboard (React + Vite)
- **Real-time Search**: Streams extraction logs directly to a `TerminalFeed` component.
- **Visualizations**: 
  - `ExpertiseRadarChart` with 4 axes: **Logic, Coding, Economics, Safety**.
  - `CrossBenchmarkTable` aggregating scores across disparate sources.
- **Comparison**: Side-by-side model comparison view with delta highlighting.
- **UX**: "Bento grid" layout, dark mode by default, and responsive design.

### Phase 1 Benchmark Scope (Enforced)

The system is configured to ONLY interact with these 6 approved sources:

| Category | Source | Metrics Extracted |
|----------|--------|-------------------|
| **General** | **HuggingFace** | MMLU, ARC, HellaSwag, TruthfulQA |
| **General** | **LMSYS Arena** | Arena ELO, Win Rate |
| **Economics**| **Vellum** | Price, Speed, Context Window |
| **Coding** | **LiveCodeBench** | Pass@1, HumanEval, MBPP |
| **Safety** | **MASK** | Lying Rate, Manipulation Score |
| **Safety** | **Vectara** | Hallucination Rate |

### Key Technical Decisions

1.  **Normalization Strategy**:
    *   All scores normalized to **0-100**.
    *   **Higher is ALWAYS better**.
    *   Negative metrics (hallucination rate) are inverted: `100 - rate`.
    *   ELO scores normalized: `((elo - 1000) / 500) * 100`.

2.  **Mino Integration**:
    *   Stateless agent pattern.
    *   One agent per benchmark source.
    *   Parallel execution for speed.

3.  **Data Consistency**:
    *   Canonical `model_id` mapping ensures `gpt-4o` matches `GPT-4o` across sources.

### Next Steps (Phase 2)
*   Implement historical data tracking (time-series).
*   Add authentication for user accounts.
*   Expand benchmark sources (if approved).

---
**Tinyfish Solutions Engineering**
