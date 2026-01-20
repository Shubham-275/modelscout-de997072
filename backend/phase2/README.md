# Model Scout: Phase 2 — Scoring Rigor & Temporal Integrity

## Overview

Phase 2 extends Model Scout with production-grade analytics infrastructure:
- **Performance Reliability Score (PRS)** — Non-ranking stability metric
- **Temporal Diff Engine** — Version-guarded snapshot comparisons
- **Regression Detection** — Threshold-based with full audit trail
- **Cost-Performance Frontier** — Tradeoff visualization with explicit normalization
- **Snapshot Integrity** — SHA-256 content hashing, immutability

## Core Principle

> **Phase 2 must never imply global authority, hidden weighting, or universal ranking.**

Any metric, visualization, or API response that could be misinterpreted as authoritative ranking is prohibited.

---

## 1. Performance Reliability Score (PRS)

### Definition

PRS ∈ [0, 100] is a **non-ranking** composite reliability metric.

```
PRS = (0.40 × CapabilityConsistency) + 
      (0.35 × BenchmarkStability) + 
      (0.25 × TemporalReliability)
```

### Components

#### A. Capability Consistency (40%)
- **Measure**: Normalized mean benchmark score across all included benchmarks
- **Normalization**: Snapshot-local (only models in the current snapshot)
- **Purpose**: How well does this model perform relative to peers in this extraction?

#### B. Benchmark Stability (35%)
- **Measure**: Inverse normalized variance over last N extractions
- **N**: 3 (default)
- **Missing Data Penalty**: 15% multiplicative penalty per missing benchmark
- **Purpose**: Are this model's scores consistent over time?

```python
# Stability Calculation
variance = mean((score - mean_score)² for each extraction)
normalized_variance = variance / 2500  # Max variance for 0-100 scale
stability = (1 - normalized_variance) * penalty_factor * extraction_coverage
```

#### C. Temporal Reliability (25%)
- **Volatility Penalty**: 
  - 0-5% change: No penalty
  - 5-20% change: Linear penalty up to 30%
  - >20% change: Severe penalty (capped at 70%)
- **Structure Penalty**: 10% per benchmark appeared/disappeared
- **Purpose**: Is this model behaving predictably between extractions?

### Hard Rules

- ❌ PRS must NOT change model ordering
- ❌ PRS must NOT be used as a leaderboard
- ✅ Raw benchmark values MUST always be accessible

### API

```http
GET /api/v2/prs/{model_id}

Response:
{
  "model_id": "openai/gpt-4o",
  "prs": {
    "final_prs": 78.5,
    "components": {
      "capability_consistency": { "value": 85.2, "weight": 0.40 },
      "benchmark_stability": { "value": 72.1, "weight": 0.35 },
      "temporal_reliability": { "value": 69.8, "weight": 0.25 }
    },
    "disclaimer": "PRS is a NON-RANKING stability metric..."
  },
  "raw_scores": { "mmlu": 88.7, "humaneval": 90.2, ... }
}
```

---

## 2. Temporal Diff Engine

### Snapshot Semantics

- **T-1** = Last successful extraction with **identical benchmark IDs + versions**
- If benchmark versions differ → Diff is **disabled** and labeled "Incomparable"
- **No cross-version comparisons allowed**

### Snapshot Structure

```python
{
  "snapshot_id": "snap_20260120T173000Z",
  "timestamp_utc": "2026-01-20T17:30:00Z",
  "model_ids": ["openai/gpt-4o", "anthropic/claude-3.5-sonnet", ...],
  "model_scores": {
    "openai/gpt-4o": {"mmlu": 88.7, "humaneval": 90.2, ...}
  },
  "benchmark_versions": [
    {"benchmark_id": "mmlu", "version": "2024-01", "source_url": "..."}
  ],
  "content_hash": "a1b2c3d4..."  // SHA-256
}
```

### API

```http
GET /api/v2/snapshots/diff

Response:
{
  "status": "comparable",  // or "incomparable_version_mismatch"
  "score_deltas": {
    "openai/gpt-4o": {"mmlu": +0.3, "humaneval": -0.1}
  },
  "explanation": "Compared 5 models across 6 benchmarks."
}
```

---

## 3. Regression Detection

### Thresholds (Defaults)

| Severity | Threshold |
|----------|-----------|
| Minor    | ≥ 5% drop |
| Major    | ≥ 10% drop |

### Category Overrides

| Category   | Minor | Major |
|------------|-------|-------|
| Reasoning  | 3%    | 7%    |
| Coding     | 7%    | 15%   |
| Safety     | 2%    | 5%    |
| Economics  | 10%   | 20%   |

### UI Requirements

Every regression flag MUST display:
- ✅ Exact delta %
- ✅ Benchmark source
- ✅ Snapshot IDs used

### API

```http
POST /api/v2/regressions/detect/{model_id}

Response:
{
  "summary": {
    "regressions_found": 2,
    "minor_regressions": 1,
    "major_regressions": 1
  },
  "events": [
    {
      "benchmark_id": "humaneval",
      "delta_percentage": -12.5,
      "severity": "major",
      "audit_trail": {
        "current_snapshot_id": "snap_20260120...",
        "previous_snapshot_id": "snap_20260119..."
      }
    }
  ]
}
```

---

## 4. Cost-Performance Frontier

### Normalization Scope (MANDATORY)

> Normalization is computed **ONLY** over the currently filtered model set.

### Axes

- **X-axis**: Cost (normalized) — 0 = cheapest in set, 1 = most expensive
- **Y-axis**: Capability (normalized) — 0 = lowest in set, 1 = highest

### Clarifications

- ❌ Frontier ≠ recommendation
- ❌ Frontier ≠ universal optimality
- ❌ Frontier ≠ ranking
- ✅ Frontier = tradeoff visualization only

### Pareto Frontier

Models on the Pareto frontier: No other model in the set is both cheaper AND more capable.

### API

```http
GET /api/v2/frontier?cost_metric=input_price&capability_metric=average_score

Response:
{
  "points": [
    {
      "model_id": "openai/gpt-4o",
      "normalized": {"cost": 0.8, "capability": 0.95},
      "is_pareto_optimal": true
    }
  ],
  "warnings": [
    "Normalization scope: Current filter only",
    "Frontier ≠ recommendation"
  ]
}
```

---

## 5. Snapshot Integrity

### Requirements

Each snapshot includes:
- Model IDs
- Benchmark IDs + versions
- Weights used
- Extraction timestamp
- **Content hash (SHA-256)**

### Properties

- ✅ Immutable — No retroactive mutation
- ✅ Diffable — Can compare sequential snapshots
- ✅ Auditable — Full provenance trail

### Verification API

```http
GET /api/v2/snapshots/{id}/verify

Response:
{
  "integrity_valid": true,
  "stored_hash": "a1b2c3d4...",
  "computed_hash": "a1b2c3d4...",
  "message": "Snapshot integrity verified."
}
```

---

## 6. Data Transparency Guarantees

| Requirement | Implementation |
|-------------|----------------|
| Raw values accessible | Every PRS response includes `raw_scores` |
| Composite scores don't hide inputs | Full component breakdown in API |
| Tooltips expose formulas | `/api/v2/docs/prs` returns formulas |
| PRS labeled as non-ranking | Disclaimer in every response |

---

## 7. Explicit Non-Goals

The following are **prohibited** in Phase 2:

- ❌ Automatic model recommendations
- ❌ "Best model" labels
- ❌ Silent normalization
- ❌ Re-ranking based on PRS
- ❌ Cross-version benchmark comparisons

---

## File Structure

```
backend/phase2/
├── __init__.py          # Module exports
├── prs.py               # PRS computation
├── snapshots.py         # Snapshot system + SHA-256
├── regression.py        # Regression detection
├── temporal.py          # Temporal diff engine
├── frontier.py          # Cost-performance frontier
├── database.py          # Phase 2 schema
└── api.py               # Flask blueprint
```

---

## Quality Bar

> If two engineers implement this independently, their outputs must match.

> If a model vendor challenges a regression, the system must be defensible.

> If data is missing or incomparable, the UI must say so explicitly.
