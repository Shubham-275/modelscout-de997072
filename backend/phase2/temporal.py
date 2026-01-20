"""
Model Scout - Phase 2: Temporal Diff Engine

TEMPORAL DIFF SEMANTICS (NON-NEGOTIABLE):
- Temporal diffs compare the most recent extraction against the 
  immediately previous extraction of the same benchmark version.
- "T-1" = last successful extraction with identical benchmark IDs + versions
- If benchmark versions differ → diff is disabled and labeled "Incomparable"
- No cross-version comparisons allowed

This prevents regression disputes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from .snapshots import Snapshot, SnapshotDiff, DiffStatus, diff_snapshots


class ExtractionStatus(Enum):
    """Status of an extraction attempt."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


@dataclass
class ExtractionRecord:
    """
    Record of a single extraction attempt.
    """
    extraction_id: str
    model_id: str
    benchmark_id: str
    benchmark_version: str
    
    status: ExtractionStatus
    scores: Dict[str, float]  # metric_name -> score
    
    timestamp_utc: str
    source_url: str
    
    # Error details if failed
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "extraction_id": self.extraction_id,
            "model_id": self.model_id,
            "benchmark_id": self.benchmark_id,
            "benchmark_version": self.benchmark_version,
            "status": self.status.value,
            "scores": self.scores,
            "timestamp_utc": self.timestamp_utc,
            "source_url": self.source_url
        }
        if self.error_code:
            result["error"] = {
                "code": self.error_code,
                "message": self.error_message
            }
        return result


@dataclass
class TemporalPair:
    """
    A pair of extractions for temporal comparison.
    """
    current: ExtractionRecord
    previous: Optional[ExtractionRecord]
    
    is_comparable: bool
    incompatibility_reason: Optional[str] = None
    
    # Delta for each metric (only if comparable)
    metric_deltas: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "current": self.current.to_dict(),
            "previous": self.previous.to_dict() if self.previous else None,
            "is_comparable": self.is_comparable,
            "incompatibility_reason": self.incompatibility_reason,
            "metric_deltas": self.metric_deltas
        }


class TemporalDiffEngine:
    """
    Engine for performing version-guarded temporal comparisons.
    
    STRICT SEMANTICS:
    - Only compares extractions with identical benchmark versions
    - Rejects cross-version comparisons
    - Tracks extraction history by model+benchmark+version
    """
    
    def __init__(self):
        # In-memory storage (would be backed by DB in production)
        # Structure: {model_id: {benchmark_id: {version: [ExtractionRecord, ...]}}}
        self._history: Dict[str, Dict[str, Dict[str, List[ExtractionRecord]]]] = {}
        
        # Snapshot storage
        self._snapshots: List[Snapshot] = []
    
    def record_extraction(self, record: ExtractionRecord) -> None:
        """
        Record an extraction for temporal tracking.
        """
        model_id = record.model_id
        benchmark_id = record.benchmark_id
        version = record.benchmark_version
        
        if model_id not in self._history:
            self._history[model_id] = {}
        
        if benchmark_id not in self._history[model_id]:
            self._history[model_id][benchmark_id] = {}
        
        if version not in self._history[model_id][benchmark_id]:
            self._history[model_id][benchmark_id][version] = []
        
        # Insert at beginning (newest first)
        self._history[model_id][benchmark_id][version].insert(0, record)
    
    def get_temporal_pair(
        self,
        model_id: str,
        benchmark_id: str,
        benchmark_version: str
    ) -> TemporalPair:
        """
        Get the current+previous extraction pair for temporal comparison.
        
        STRICT DEFINITION:
        - "T-1" = last successful extraction with identical benchmark version
        
        Returns:
            TemporalPair with comparability status and deltas
        """
        history = self._history.get(model_id, {}).get(benchmark_id, {}).get(benchmark_version, [])
        
        # Find current (most recent successful)
        current = None
        for record in history:
            if record.status == ExtractionStatus.SUCCESS:
                current = record
                break
        
        if current is None:
            # No successful extraction found
            raise ValueError(f"No successful extraction found for {model_id}/{benchmark_id}/{benchmark_version}")
        
        # Find previous (next most recent successful, SAME version)
        previous = None
        found_current = False
        for record in history:
            if record.extraction_id == current.extraction_id:
                found_current = True
                continue
            if found_current and record.status == ExtractionStatus.SUCCESS:
                previous = record
                break
        
        if previous is None:
            return TemporalPair(
                current=current,
                previous=None,
                is_comparable=False,
                incompatibility_reason="No previous extraction with same benchmark version"
            )
        
        # Verify versions match (should be same by construction, but double-check)
        if current.benchmark_version != previous.benchmark_version:
            return TemporalPair(
                current=current,
                previous=previous,
                is_comparable=False,
                incompatibility_reason=f"Version mismatch: {current.benchmark_version} vs {previous.benchmark_version}"
            )
        
        # Compute metric deltas
        metric_deltas = {}
        common_metrics = set(current.scores.keys()) & set(previous.scores.keys())
        
        for metric in common_metrics:
            curr_val = current.scores[metric]
            prev_val = previous.scores[metric]
            metric_deltas[metric] = curr_val - prev_val
        
        return TemporalPair(
            current=current,
            previous=previous,
            is_comparable=True,
            metric_deltas=metric_deltas
        )
    
    def get_extraction_history(
        self,
        model_id: str,
        benchmark_id: str,
        version: Optional[str] = None,
        limit: int = 10
    ) -> List[ExtractionRecord]:
        """
        Get extraction history for a model/benchmark.
        
        Args:
            model_id: Model identifier
            benchmark_id: Benchmark identifier
            version: Optional version filter (all versions if None)
            limit: Max records to return
            
        Returns:
            List of ExtractionRecords, newest first
        """
        model_history = self._history.get(model_id, {}).get(benchmark_id, {})
        
        if version:
            records = model_history.get(version, [])
        else:
            # Combine all versions, sorted by timestamp
            records = []
            for version_records in model_history.values():
                records.extend(version_records)
            records.sort(key=lambda r: r.timestamp_utc, reverse=True)
        
        return records[:limit]
    
    def record_snapshot(self, snapshot: Snapshot) -> None:
        """Add a snapshot to the history."""
        self._snapshots.append(snapshot)
        self._snapshots.sort(key=lambda s: s.timestamp_utc, reverse=True)
    
    def get_latest_snapshots(self, count: int = 2) -> List[Snapshot]:
        """Get the N most recent snapshots."""
        return self._snapshots[:count]
    
    def diff_latest_snapshots(self) -> SnapshotDiff:
        """
        Diff the two most recent snapshots.
        
        Returns:
            SnapshotDiff with version-guarded comparison
        """
        snapshots = self.get_latest_snapshots(2)
        
        if len(snapshots) == 0:
            raise ValueError("No snapshots available")
        
        current = snapshots[0]
        previous = snapshots[1] if len(snapshots) > 1 else None
        
        return diff_snapshots(current, previous)
    
    def get_model_timeline(
        self,
        model_id: str,
        benchmark_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get complete timeline for a model across all benchmarks/versions.
        
        Returns:
            Dict with timeline data and version boundaries
        """
        model_history = self._history.get(model_id, {})
        
        timeline = {
            "model_id": model_id,
            "benchmarks": {}
        }
        
        for bench_id, version_history in model_history.items():
            if benchmark_id and bench_id != benchmark_id:
                continue
            
            timeline["benchmarks"][bench_id] = {
                "versions": {}
            }
            
            for version, records in version_history.items():
                timeline["benchmarks"][bench_id]["versions"][version] = {
                    "extraction_count": len(records),
                    "latest": records[0].to_dict() if records else None,
                    "oldest": records[-1].to_dict() if records else None,
                    "success_rate": sum(1 for r in records if r.status == ExtractionStatus.SUCCESS) / len(records) if records else 0
                }
        
        return timeline


# Singleton instance for the application
_engine: Optional[TemporalDiffEngine] = None


def get_temporal_engine() -> TemporalDiffEngine:
    """Get the global temporal diff engine instance."""
    global _engine
    if _engine is None:
        _engine = TemporalDiffEngine()
    return _engine
