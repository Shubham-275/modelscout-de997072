"""
Model Scout - Phase 2: Snapshot System

SNAPSHOT SEMANTICS (NON-NEGOTIABLE):
- All snapshots must be cryptographically verifiable
- Each snapshot includes: Model IDs, Benchmark IDs + versions, Weights used,
  Extraction timestamp, Content hash (SHA-256)
- Snapshots are: Immutable, Diffable, Auditable
- No retroactive mutation

TEMPORAL DIFF DEFINITION:
"T-1" = last successful extraction with identical benchmark IDs + versions
If benchmark versions differ → diff is disabled and labeled "Incomparable"
No cross-version comparisons allowed
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum


class DiffStatus(Enum):
    """Status of a temporal diff operation."""
    COMPARABLE = "comparable"
    INCOMPARABLE_VERSION_MISMATCH = "incomparable_version_mismatch"
    INCOMPARABLE_BENCHMARK_MISMATCH = "incomparable_benchmark_mismatch"
    NO_PREVIOUS_SNAPSHOT = "no_previous_snapshot"


@dataclass
class BenchmarkVersion:
    """Tracks benchmark source and version for comparability checks."""
    benchmark_id: str
    version: str  # e.g., "2024-01" or commit hash
    source_url: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "benchmark_id": self.benchmark_id,
            "version": self.version,
            "source_url": self.source_url
        }


@dataclass
class Snapshot:
    """
    Immutable, hashable snapshot of model benchmark data.
    
    Integrity Requirements:
    - Content hash (SHA-256) computed over deterministic JSON
    - No retroactive mutation allowed
    - All fields required for audit
    """
    snapshot_id: str
    timestamp_utc: str
    
    # Model data
    model_ids: List[str]
    model_scores: Dict[str, Dict[str, float]]  # model_id -> {benchmark -> score}
    
    # Benchmark metadata
    benchmark_versions: List[BenchmarkVersion]
    
    # Weights used for any composite calculations
    weights_used: Dict[str, float]
    
    # Integrity
    content_hash: str = ""
    
    # Metadata
    extraction_source: str = "mino"
    phase: str = "phase-2"
    
    def __post_init__(self):
        """Compute content hash after initialization."""
        if not self.content_hash:
            self.content_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """
        Compute SHA-256 hash of snapshot content.
        Uses deterministic JSON serialization for reproducibility.
        """
        # Create deterministic representation
        hashable_content = {
            "snapshot_id": self.snapshot_id,
            "timestamp_utc": self.timestamp_utc,
            "model_ids": sorted(self.model_ids),
            "model_scores": {
                k: dict(sorted(v.items()))
                for k, v in sorted(self.model_scores.items())
            },
            "benchmark_versions": [
                bv.to_dict() for bv in sorted(
                    self.benchmark_versions, key=lambda x: x.benchmark_id
                )
            ],
            "weights_used": dict(sorted(self.weights_used.items()))
        }
        
        # Deterministic JSON
        json_str = json.dumps(hashable_content, sort_keys=True, separators=(',', ':'))
        
        # SHA-256
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify snapshot has not been mutated."""
        expected_hash = self._compute_hash()
        return self.content_hash == expected_hash
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize snapshot for storage/API."""
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp_utc": self.timestamp_utc,
            "model_ids": self.model_ids,
            "model_scores": self.model_scores,
            "benchmark_versions": [bv.to_dict() for bv in self.benchmark_versions],
            "weights_used": self.weights_used,
            "content_hash": self.content_hash,
            "extraction_source": self.extraction_source,
            "phase": self.phase,
            "integrity_verified": self.verify_integrity()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Snapshot":
        """Deserialize snapshot from storage."""
        benchmark_versions = [
            BenchmarkVersion(**bv) for bv in data.get("benchmark_versions", [])
        ]
        
        snapshot = cls(
            snapshot_id=data["snapshot_id"],
            timestamp_utc=data["timestamp_utc"],
            model_ids=data["model_ids"],
            model_scores=data["model_scores"],
            benchmark_versions=benchmark_versions,
            weights_used=data.get("weights_used", {}),
            content_hash=data.get("content_hash", ""),
            extraction_source=data.get("extraction_source", "mino"),
            phase=data.get("phase", "phase-2")
        )
        
        return snapshot


@dataclass
class SnapshotDiff:
    """
    Result of comparing two snapshots.
    
    EXPLICIT CONSTRAINTS:
    - "T-1" = last successful extraction with identical benchmark IDs + versions
    - If benchmark versions differ → diff is disabled and labeled "Incomparable"
    - No cross-version comparisons allowed
    """
    status: DiffStatus
    current_snapshot_id: str
    previous_snapshot_id: Optional[str]
    
    # Score differences (only if COMPARABLE)
    score_deltas: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # model_id -> {benchmark -> delta}
    
    # Explanation for status
    explanation: str = ""
    
    # Mismatched versions (for debugging)
    version_mismatches: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "current_snapshot_id": self.current_snapshot_id,
            "previous_snapshot_id": self.previous_snapshot_id,
            "score_deltas": self.score_deltas,
            "explanation": self.explanation,
            "version_mismatches": self.version_mismatches,
            "is_comparable": self.status == DiffStatus.COMPARABLE
        }


def create_snapshot(
    model_scores: Dict[str, Dict[str, float]],
    benchmark_versions: List[BenchmarkVersion],
    weights_used: Optional[Dict[str, float]] = None
) -> Snapshot:
    """
    Create a new immutable snapshot.
    
    Args:
        model_scores: Dict of model_id -> {benchmark_name -> score}
        benchmark_versions: List of BenchmarkVersion for each benchmark
        weights_used: Optional weights used for composite calculations
        
    Returns:
        New Snapshot with computed hash
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    snapshot_id = f"snap_{timestamp.replace(':', '').replace('-', '').replace('.', '_')}"
    
    return Snapshot(
        snapshot_id=snapshot_id,
        timestamp_utc=timestamp,
        model_ids=sorted(model_scores.keys()),
        model_scores=model_scores,
        benchmark_versions=benchmark_versions,
        weights_used=weights_used or {}
    )


def verify_snapshot(snapshot: Snapshot) -> Tuple[bool, str]:
    """
    Verify snapshot integrity.
    
    Returns:
        Tuple of (is_valid, message)
    """
    if snapshot.verify_integrity():
        return True, f"Snapshot {snapshot.snapshot_id} integrity verified. Hash: {snapshot.content_hash[:16]}..."
    else:
        expected = snapshot._compute_hash()
        return False, f"INTEGRITY VIOLATION: Expected {expected[:16]}..., got {snapshot.content_hash[:16]}..."


def diff_snapshots(
    current: Snapshot,
    previous: Optional[Snapshot]
) -> SnapshotDiff:
    """
    Compute temporal diff between two snapshots.
    
    STRICT SEMANTICS:
    - If benchmark versions differ → diff is disabled
    - No cross-version comparisons allowed
    
    Args:
        current: Current snapshot
        previous: Previous snapshot (None if first)
        
    Returns:
        SnapshotDiff with status and deltas (if comparable)
    """
    if previous is None:
        return SnapshotDiff(
            status=DiffStatus.NO_PREVIOUS_SNAPSHOT,
            current_snapshot_id=current.snapshot_id,
            previous_snapshot_id=None,
            explanation="No previous snapshot available for comparison."
        )
    
    # Check benchmark version compatibility
    current_versions = {bv.benchmark_id: bv for bv in current.benchmark_versions}
    previous_versions = {bv.benchmark_id: bv for bv in previous.benchmark_versions}
    
    version_mismatches = []
    
    # Check for version mismatches
    common_benchmarks = set(current_versions.keys()) & set(previous_versions.keys())
    for benchmark_id in common_benchmarks:
        curr_v = current_versions[benchmark_id]
        prev_v = previous_versions[benchmark_id]
        
        if curr_v.version != prev_v.version:
            version_mismatches.append({
                "benchmark_id": benchmark_id,
                "current_version": curr_v.version,
                "previous_version": prev_v.version
            })
    
    if version_mismatches:
        return SnapshotDiff(
            status=DiffStatus.INCOMPARABLE_VERSION_MISMATCH,
            current_snapshot_id=current.snapshot_id,
            previous_snapshot_id=previous.snapshot_id,
            explanation=f"Cannot compare: {len(version_mismatches)} benchmark(s) have different versions. Cross-version comparison is prohibited.",
            version_mismatches=version_mismatches
        )
    
    # Check for benchmark set mismatch
    current_benchmark_ids = set(current_versions.keys())
    previous_benchmark_ids = set(previous_versions.keys())
    
    if current_benchmark_ids != previous_benchmark_ids:
        added = current_benchmark_ids - previous_benchmark_ids
        removed = previous_benchmark_ids - current_benchmark_ids
        
        return SnapshotDiff(
            status=DiffStatus.INCOMPARABLE_BENCHMARK_MISMATCH,
            current_snapshot_id=current.snapshot_id,
            previous_snapshot_id=previous.snapshot_id,
            explanation=f"Benchmark set changed. Added: {list(added)}, Removed: {list(removed)}. Comparison disabled."
        )
    
    # Compute score deltas
    score_deltas: Dict[str, Dict[str, float]] = {}
    
    common_models = set(current.model_ids) & set(previous.model_ids)
    
    for model_id in common_models:
        curr_scores = current.model_scores.get(model_id, {})
        prev_scores = previous.model_scores.get(model_id, {})
        
        model_deltas = {}
        for benchmark in common_benchmarks:
            curr_score = curr_scores.get(benchmark)
            prev_score = prev_scores.get(benchmark)
            
            if curr_score is not None and prev_score is not None:
                model_deltas[benchmark] = curr_score - prev_score
        
        if model_deltas:
            score_deltas[model_id] = model_deltas
    
    return SnapshotDiff(
        status=DiffStatus.COMPARABLE,
        current_snapshot_id=current.snapshot_id,
        previous_snapshot_id=previous.snapshot_id,
        score_deltas=score_deltas,
        explanation=f"Compared {len(common_models)} models across {len(common_benchmarks)} benchmarks."
    )
