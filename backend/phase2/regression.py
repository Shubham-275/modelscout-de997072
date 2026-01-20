"""
Model Scout - Phase 2: Regression Detection

REGRESSION DEFINITIONS (DETERMINISTIC):
- Regression = capability drop exceeding a defined threshold
- Thresholds are:
  - Default: 5% (minor), 10% (major)
  - User-overridable
  - Benchmark-category aware (e.g. reasoning vs coding)

UI REQUIREMENTS:
- Show exact delta %
- Show benchmark source
- Show snapshot IDs used
- No silent flags

All regression detections must be explainable.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class RegressionSeverity(Enum):
    """Severity levels for regressions."""
    NONE = "none"
    MINOR = "minor"      # 5-10% drop
    MAJOR = "major"      # >10% drop


@dataclass
class RegressionThresholds:
    """
    Configurable thresholds for regression detection.
    
    Default values:
    - minor_threshold: 5% (capability drop >= 5% triggers minor)
    - major_threshold: 10% (capability drop >= 10% triggers major)
    
    Thresholds can be overridden per benchmark category.
    """
    minor_threshold_pct: float = 5.0
    major_threshold_pct: float = 10.0
    
    # Category-specific overrides
    category_overrides: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        # Reasoning benchmarks tend to be more stable
        "reasoning": {"minor": 3.0, "major": 7.0},
        # Coding benchmarks can be volatile
        "coding": {"minor": 7.0, "major": 15.0},
        # Safety benchmarks are critical
        "safety": {"minor": 2.0, "major": 5.0},
        # Economics (cost/speed) can fluctuate
        "economics": {"minor": 10.0, "major": 20.0}
    })
    
    def get_thresholds(self, category: Optional[str] = None) -> tuple:
        """
        Get (minor, major) thresholds for a category.
        
        Returns:
            Tuple of (minor_threshold_pct, major_threshold_pct)
        """
        if category and category.lower() in self.category_overrides:
            overrides = self.category_overrides[category.lower()]
            return overrides.get("minor", self.minor_threshold_pct), overrides.get("major", self.major_threshold_pct)
        return self.minor_threshold_pct, self.major_threshold_pct
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "default_minor_threshold_pct": self.minor_threshold_pct,
            "default_major_threshold_pct": self.major_threshold_pct,
            "category_overrides": self.category_overrides
        }


@dataclass
class RegressionEvent:
    """
    A single regression event with full audit trail.
    
    UI REQUIREMENTS:
    - Show exact delta %
    - Show benchmark source
    - Show snapshot IDs used
    """
    model_id: str
    benchmark_id: str
    benchmark_category: str
    
    # Scores
    current_score: float
    previous_score: float
    delta_absolute: float
    delta_percentage: float
    
    # Severity
    severity: RegressionSeverity
    
    # Thresholds used (for transparency)
    thresholds_used: Dict[str, float]
    
    # Snapshot audit trail
    current_snapshot_id: str
    previous_snapshot_id: str
    
    # Timestamp
    detected_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "benchmark": {
                "id": self.benchmark_id,
                "category": self.benchmark_category
            },
            "scores": {
                "current": round(self.current_score, 2),
                "previous": round(self.previous_score, 2),
                "delta_absolute": round(self.delta_absolute, 2),
                "delta_percentage": round(self.delta_percentage, 2)
            },
            "severity": self.severity.value,
            "is_regression": self.severity != RegressionSeverity.NONE,
            "thresholds_used": self.thresholds_used,
            "audit_trail": {
                "current_snapshot_id": self.current_snapshot_id,
                "previous_snapshot_id": self.previous_snapshot_id,
                "detected_at": self.detected_at
            },
            "explanation": self._generate_explanation()
        }
    
    def _generate_explanation(self) -> str:
        """Generate human-readable explanation."""
        if self.severity == RegressionSeverity.NONE:
            if self.delta_percentage > 0:
                return f"Score improved by {abs(self.delta_percentage):.1f}%"
            return f"Score stable (change: {self.delta_percentage:.1f}%)"
        
        severity_word = "MAJOR" if self.severity == RegressionSeverity.MAJOR else "Minor"
        return (
            f"{severity_word} regression detected: {self.benchmark_id} dropped {abs(self.delta_percentage):.1f}% "
            f"(from {self.previous_score:.1f} to {self.current_score:.1f}). "
            f"Threshold: {self.thresholds_used.get('minor' if self.severity == RegressionSeverity.MINOR else 'major', 0):.1f}%"
        )


@dataclass
class RegressionReport:
    """
    Complete regression analysis report.
    """
    model_id: str
    total_benchmarks_analyzed: int
    regressions_found: int
    minor_regressions: int
    major_regressions: int
    
    events: List[RegressionEvent]
    
    thresholds: RegressionThresholds
    
    current_snapshot_id: str
    previous_snapshot_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "summary": {
                "benchmarks_analyzed": self.total_benchmarks_analyzed,
                "regressions_found": self.regressions_found,
                "minor_regressions": self.minor_regressions,
                "major_regressions": self.major_regressions,
                "has_major_regression": self.major_regressions > 0
            },
            "events": [e.to_dict() for e in self.events],
            "thresholds_config": self.thresholds.to_dict(),
            "snapshots": {
                "current": self.current_snapshot_id,
                "previous": self.previous_snapshot_id
            }
        }


# Benchmark category mapping
BENCHMARK_CATEGORIES: Dict[str, str] = {
    # HuggingFace benchmarks
    "mmlu": "reasoning",
    "arc_challenge": "reasoning",
    "hellaswag": "reasoning",
    "truthfulqa": "reasoning",
    "winogrande": "reasoning",
    "gsm8k": "reasoning",
    
    # Coding benchmarks
    "humaneval": "coding",
    "mbpp": "coding",
    "pass_at_1": "coding",
    
    # Arena
    "arena_elo": "reasoning",
    
    # Safety benchmarks
    "hallucination_rate": "safety",
    "lying_rate": "safety",
    "manipulation_score": "safety",
    "deception_score": "safety",
    
    # Economics benchmarks
    "input_price": "economics",
    "output_price": "economics",
    "speed_tps": "economics",
    "latency_ms": "economics",
    "context_window": "economics"
}


def get_benchmark_category(benchmark_id: str) -> str:
    """Get category for a benchmark ID."""
    return BENCHMARK_CATEGORIES.get(benchmark_id.lower(), "general")


def detect_regressions(
    model_id: str,
    current_scores: Dict[str, float],
    previous_scores: Dict[str, float],
    current_snapshot_id: str,
    previous_snapshot_id: str,
    thresholds: Optional[RegressionThresholds] = None,
    detection_timestamp: Optional[str] = None
) -> RegressionReport:
    """
    Detect regressions between two score sets.
    
    DETERMINISTIC LOGIC:
    1. For each common benchmark, compute delta %
    2. Compare against category-aware thresholds
    3. Flag as minor/major/none based on threshold breach
    
    Args:
        model_id: Canonical model identifier
        current_scores: Current benchmark scores
        previous_scores: Previous benchmark scores
        current_snapshot_id: ID of current snapshot
        previous_snapshot_id: ID of previous snapshot
        thresholds: Optional custom thresholds (defaults used if None)
        detection_timestamp: Optional timestamp (current time if None)
        
    Returns:
        RegressionReport with all events and summary
    """
    from datetime import datetime
    
    if thresholds is None:
        thresholds = RegressionThresholds()
    
    if detection_timestamp is None:
        detection_timestamp = datetime.utcnow().isoformat() + "Z"
    
    events: List[RegressionEvent] = []
    minor_count = 0
    major_count = 0
    
    # Analyze common benchmarks
    common_benchmarks = set(current_scores.keys()) & set(previous_scores.keys())
    
    for benchmark_id in common_benchmarks:
        current = current_scores[benchmark_id]
        previous = previous_scores[benchmark_id]
        
        # Skip if previous is 0 (avoid division by zero)
        if previous == 0:
            continue
        
        # Compute delta
        delta_absolute = current - previous
        delta_percentage = (delta_absolute / previous) * 100
        
        # Get category and thresholds
        category = get_benchmark_category(benchmark_id)
        minor_thresh, major_thresh = thresholds.get_thresholds(category)
        
        # Determine severity (only negative deltas are regressions)
        if delta_percentage <= -major_thresh:
            severity = RegressionSeverity.MAJOR
            major_count += 1
        elif delta_percentage <= -minor_thresh:
            severity = RegressionSeverity.MINOR
            minor_count += 1
        else:
            severity = RegressionSeverity.NONE
        
        event = RegressionEvent(
            model_id=model_id,
            benchmark_id=benchmark_id,
            benchmark_category=category,
            current_score=current,
            previous_score=previous,
            delta_absolute=delta_absolute,
            delta_percentage=delta_percentage,
            severity=severity,
            thresholds_used={"minor": minor_thresh, "major": major_thresh},
            current_snapshot_id=current_snapshot_id,
            previous_snapshot_id=previous_snapshot_id,
            detected_at=detection_timestamp
        )
        
        events.append(event)
    
    return RegressionReport(
        model_id=model_id,
        total_benchmarks_analyzed=len(common_benchmarks),
        regressions_found=minor_count + major_count,
        minor_regressions=minor_count,
        major_regressions=major_count,
        events=events,
        thresholds=thresholds,
        current_snapshot_id=current_snapshot_id,
        previous_snapshot_id=previous_snapshot_id
    )
