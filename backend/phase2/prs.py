"""
Model Scout - Phase 2: Performance Reliability Score (PRS)

FORMAL DEFINITION:
PRS ∈ [0, 100], computed as a weighted composite of:
- A. Capability Consistency (40%) - Normalized mean benchmark score
- B. Benchmark Stability (35%) - Inverse normalized variance over N extractions
- C. Temporal Reliability (25%) - Penalizes volatility and appearance/disappearance

PRS is a NON-RANKING metric. It does not reorder models or imply preference.
It is a stability & trust signal only.

HARD RULES:
- PRS must not change model ordering
- PRS must not be used as a leaderboard
- Raw benchmark values must always be accessible within one click
"""

import math
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# =============================================================================
# CONSTANTS — FIXED WEIGHTS (DO NOT MODIFY WITHOUT SPEC CHANGE)
# =============================================================================

WEIGHT_CAPABILITY_CONSISTENCY = 0.40
WEIGHT_BENCHMARK_STABILITY = 0.35
WEIGHT_TEMPORAL_RELIABILITY = 0.25

# Default number of recent extractions for stability calculation
DEFAULT_STABILITY_WINDOW = 3

# Missing data penalty multiplier
MISSING_DATA_PENALTY = 0.85  # 15% penalty per missing benchmark


@dataclass
class PRSComponents:
    """
    Breakdown of PRS computation for transparency.
    All values are in [0, 100] range.
    """
    capability_consistency: float
    benchmark_stability: float
    temporal_reliability: float
    final_prs: float
    
    # Audit trail
    benchmarks_included: List[str] = field(default_factory=list)
    extraction_count: int = 0
    missing_benchmarks: List[str] = field(default_factory=list)
    computation_timestamp: str = ""
    
    # Formula transparency
    formula: str = (
        "PRS = (0.40 × CapabilityConsistency) + "
        "(0.35 × BenchmarkStability) + "
        "(0.25 × TemporalReliability)"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for API response with full transparency."""
        return {
            "final_prs": round(self.final_prs, 2),
            "components": {
                "capability_consistency": {
                    "value": round(self.capability_consistency, 2),
                    "weight": WEIGHT_CAPABILITY_CONSISTENCY,
                    "weighted_contribution": round(
                        self.capability_consistency * WEIGHT_CAPABILITY_CONSISTENCY, 2
                    ),
                    "definition": "Normalized mean benchmark score across all included benchmarks (snapshot-local normalization)"
                },
                "benchmark_stability": {
                    "value": round(self.benchmark_stability, 2),
                    "weight": WEIGHT_BENCHMARK_STABILITY,
                    "weighted_contribution": round(
                        self.benchmark_stability * WEIGHT_BENCHMARK_STABILITY, 2
                    ),
                    "definition": f"Inverse normalized variance over last {DEFAULT_STABILITY_WINDOW} extractions"
                },
                "temporal_reliability": {
                    "value": round(self.temporal_reliability, 2),
                    "weight": WEIGHT_TEMPORAL_RELIABILITY,
                    "weighted_contribution": round(
                        self.temporal_reliability * WEIGHT_TEMPORAL_RELIABILITY, 2
                    ),
                    "definition": "Penalizes sudden score volatility and benchmark appearance/disappearance"
                }
            },
            "audit": {
                "benchmarks_included": self.benchmarks_included,
                "extraction_count": self.extraction_count,
                "missing_benchmarks": self.missing_benchmarks,
                "computation_timestamp": self.computation_timestamp,
                "formula": self.formula
            },
            "disclaimer": "PRS is a NON-RANKING stability metric. It does not imply model preference or quality ordering."
        }


def compute_capability_consistency(
    current_scores: Dict[str, float],
    all_model_scores: Dict[str, Dict[str, float]]
) -> Tuple[float, List[str]]:
    """
    Compute Capability Consistency (40% of PRS).
    
    FORMAL DEFINITION:
    Normalized mean benchmark score across all included benchmarks.
    Normalization scope: Snapshot-local (only models present in the snapshot).
    
    Args:
        current_scores: Dict of benchmark_name -> score for target model
        all_model_scores: Dict of model_id -> {benchmark_name -> score} for all models in snapshot
        
    Returns:
        Tuple of (capability_consistency_score, list_of_benchmarks_included)
    """
    if not current_scores:
        return 0.0, []
    
    benchmarks_included = list(current_scores.keys())
    normalized_scores = []
    
    for benchmark, score in current_scores.items():
        # Collect all scores for this benchmark across models in snapshot
        benchmark_scores = [
            model_scores.get(benchmark)
            for model_scores in all_model_scores.values()
            if model_scores.get(benchmark) is not None
        ]
        
        if not benchmark_scores:
            continue
            
        # Snapshot-local min-max normalization
        min_score = min(benchmark_scores)
        max_score = max(benchmark_scores)
        
        if max_score == min_score:
            # All models have same score for this benchmark
            normalized = 1.0 if score == max_score else 0.0
        else:
            normalized = (score - min_score) / (max_score - min_score)
        
        normalized_scores.append(normalized)
    
    if not normalized_scores:
        return 0.0, benchmarks_included
    
    # Mean of normalized scores, scaled to 0-100
    capability_consistency = (sum(normalized_scores) / len(normalized_scores)) * 100
    
    return capability_consistency, benchmarks_included


def compute_benchmark_stability(
    extraction_history: List[Dict[str, float]],
    expected_benchmarks: List[str]
) -> Tuple[float, int, List[str]]:
    """
    Compute Benchmark Stability (35% of PRS).
    
    STRICT DEFINITION (from spec):
    The inverse normalized variance of a model's normalized benchmark scores 
    across the last N extractions.
    
    Formal definition:
    1. Default N = 3 most recent successful extractions
    2. Compute variance of normalized scores per benchmark
    3. Aggregate variance across benchmarks
    4. Invert and normalize to [0,1]
    
    Missing data penalty:
    - Any missing benchmark run reduces stability multiplicatively
    - Extraction failures count as missing
    
    Args:
        extraction_history: List of {benchmark -> score} dicts, newest first
        expected_benchmarks: List of benchmark names that should be present
        
    Returns:
        Tuple of (stability_score, extraction_count, missing_benchmarks)
    """
    if not extraction_history:
        return 0.0, 0, expected_benchmarks
    
    # Take last N extractions
    history = extraction_history[:DEFAULT_STABILITY_WINDOW]
    extraction_count = len(history)
    
    # Track missing benchmarks
    missing_benchmarks = set(expected_benchmarks)
    benchmark_variances = []
    
    for benchmark in expected_benchmarks:
        scores = []
        for extraction in history:
            score = extraction.get(benchmark)
            if score is not None:
                scores.append(score)
                missing_benchmarks.discard(benchmark)
        
        if len(scores) >= 2:
            # Compute variance
            mean = sum(scores) / len(scores)
            variance = sum((s - mean) ** 2 for s in scores) / len(scores)
            
            # Normalize variance (assuming scores are 0-100)
            # Max possible variance for 0-100 range is 2500 (0 and 100)
            normalized_variance = variance / 2500
            benchmark_variances.append(normalized_variance)
        elif len(scores) == 1:
            # Single score = perfect stability for this benchmark
            benchmark_variances.append(0.0)
        # If no scores, benchmark is missing
    
    if not benchmark_variances:
        return 0.0, extraction_count, list(missing_benchmarks)
    
    # Aggregate variance (mean of variances)
    aggregate_variance = sum(benchmark_variances) / len(benchmark_variances)
    
    # Invert: high variance = low stability
    # stability = 1 - aggregate_variance (clamped to [0, 1])
    raw_stability = 1.0 - min(1.0, aggregate_variance)
    
    # Apply missing data penalty multiplicatively
    penalty_factor = MISSING_DATA_PENALTY ** len(missing_benchmarks)
    stability_with_penalty = raw_stability * penalty_factor
    
    # Also penalize for having fewer than N extractions
    extraction_penalty = extraction_count / DEFAULT_STABILITY_WINDOW
    final_stability = stability_with_penalty * extraction_penalty
    
    # Scale to 0-100
    return final_stability * 100, extraction_count, list(missing_benchmarks)


def compute_temporal_reliability(
    current_scores: Dict[str, float],
    previous_scores: Optional[Dict[str, float]],
    current_benchmarks: List[str],
    previous_benchmarks: Optional[List[str]]
) -> float:
    """
    Compute Temporal Reliability (25% of PRS).
    
    DEFINITION:
    Measures short-term trustworthiness by penalizing:
    - Sudden score volatility between extractions
    - Benchmark appearance/disappearance
    - Unexplained benchmark version drift (detected via benchmark ID changes)
    
    Args:
        current_scores: Current extraction scores
        previous_scores: Previous extraction scores (None if first extraction)
        current_benchmarks: List of benchmark IDs in current extraction
        previous_benchmarks: List of benchmark IDs in previous extraction
        
    Returns:
        Temporal reliability score in [0, 100]
    """
    if previous_scores is None or previous_benchmarks is None:
        # First extraction: moderate reliability (we have no history)
        return 50.0
    
    penalties = []
    
    # 1. Score volatility penalty
    common_benchmarks = set(current_scores.keys()) & set(previous_scores.keys())
    for benchmark in common_benchmarks:
        curr = current_scores[benchmark]
        prev = previous_scores[benchmark]
        
        if prev > 0:
            # Percentage change
            pct_change = abs(curr - prev) / prev * 100
            
            # Penalty increases with volatility
            # 0-5% change = 0 penalty
            # 5-20% change = linear penalty
            # >20% change = severe penalty
            if pct_change <= 5:
                penalty = 0.0
            elif pct_change <= 20:
                penalty = (pct_change - 5) / 15 * 0.3  # Max 30% penalty
            else:
                penalty = 0.3 + (min(pct_change, 50) - 20) / 30 * 0.4  # Cap at 70%
            
            penalties.append(penalty)
    
    # 2. Benchmark appearance/disappearance penalty
    current_set = set(current_benchmarks)
    previous_set = set(previous_benchmarks)
    
    appeared = current_set - previous_set
    disappeared = previous_set - current_set
    
    # Each appearance/disappearance adds 10% penalty
    structure_penalty = (len(appeared) + len(disappeared)) * 0.10
    structure_penalty = min(structure_penalty, 0.5)  # Cap at 50%
    
    # Combine penalties
    if penalties:
        volatility_penalty = sum(penalties) / len(penalties)
    else:
        volatility_penalty = 0.0
    
    total_penalty = volatility_penalty + structure_penalty
    total_penalty = min(total_penalty, 1.0)  # Never go below 0
    
    reliability = (1.0 - total_penalty) * 100
    return max(0.0, reliability)


def compute_prs(
    model_id: str,
    current_scores: Dict[str, float],
    all_model_scores: Dict[str, Dict[str, float]],
    extraction_history: List[Dict[str, float]],
    expected_benchmarks: List[str],
    previous_scores: Optional[Dict[str, float]] = None,
    previous_benchmarks: Optional[List[str]] = None
) -> PRSComponents:
    """
    Compute Performance Reliability Score (PRS) for a model.
    
    PRS ∈ [0, 100], computed as:
    PRS = (0.40 × CapabilityConsistency) + 
          (0.35 × BenchmarkStability) + 
          (0.25 × TemporalReliability)
    
    This is a NON-RANKING metric. It does not reorder models.
    
    Args:
        model_id: Canonical model identifier
        current_scores: Dict of benchmark_name -> score for target model
        all_model_scores: Dict of model_id -> {benchmark_name -> score} for snapshot
        extraction_history: List of historical {benchmark -> score} dicts
        expected_benchmarks: List of benchmark names expected to be present
        previous_scores: Scores from immediately previous extraction
        previous_benchmarks: Benchmark list from previous extraction
        
    Returns:
        PRSComponents with full breakdown and audit trail
    """
    # A. Capability Consistency (40%)
    capability_consistency, benchmarks_included = compute_capability_consistency(
        current_scores, all_model_scores
    )
    
    # B. Benchmark Stability (35%)
    benchmark_stability, extraction_count, missing_benchmarks = compute_benchmark_stability(
        extraction_history, expected_benchmarks
    )
    
    # C. Temporal Reliability (25%)
    temporal_reliability = compute_temporal_reliability(
        current_scores,
        previous_scores,
        list(current_scores.keys()),
        previous_benchmarks
    )
    
    # Compute final PRS
    final_prs = (
        WEIGHT_CAPABILITY_CONSISTENCY * capability_consistency +
        WEIGHT_BENCHMARK_STABILITY * benchmark_stability +
        WEIGHT_TEMPORAL_RELIABILITY * temporal_reliability
    )
    
    # Clamp to [0, 100]
    final_prs = max(0.0, min(100.0, final_prs))
    
    return PRSComponents(
        capability_consistency=capability_consistency,
        benchmark_stability=benchmark_stability,
        temporal_reliability=temporal_reliability,
        final_prs=final_prs,
        benchmarks_included=benchmarks_included,
        extraction_count=extraction_count,
        missing_benchmarks=missing_benchmarks,
        computation_timestamp=datetime.utcnow().isoformat() + "Z"
    )
