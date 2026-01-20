"""
Model Scout - Phase 2 Modules
Performance Reliability Score, Temporal Diff, Regression Detection, Snapshot Integrity, Frontier
"""

from .prs import compute_prs, PRSComponents
from .snapshots import (
    create_snapshot, 
    verify_snapshot, 
    diff_snapshots,
    Snapshot,
    SnapshotDiff,
    DiffStatus,
    BenchmarkVersion
)
from .regression import (
    detect_regressions, 
    RegressionThresholds,
    RegressionReport,
    RegressionEvent,
    RegressionSeverity
)
from .temporal import (
    TemporalDiffEngine,
    get_temporal_engine,
    ExtractionRecord,
    ExtractionStatus,
    TemporalPair
)
from .frontier import (
    compute_frontier,
    compute_multi_frontier,
    FrontierChart,
    FrontierPoint
)
from .database import (
    init_phase2_schema,
    save_snapshot,
    get_snapshot,
    get_latest_snapshots,
    save_extraction_record,
    get_extraction_history,
    save_regression_event,
    get_regression_history,
    save_prs_record,
    get_prs_history
)

__all__ = [
    # PRS
    'compute_prs',
    'PRSComponents',
    
    # Snapshots
    'create_snapshot',
    'verify_snapshot',
    'diff_snapshots',
    'Snapshot',
    'SnapshotDiff',
    'DiffStatus',
    'BenchmarkVersion',
    
    # Regression
    'detect_regressions',
    'RegressionThresholds',
    'RegressionReport',
    'RegressionEvent',
    'RegressionSeverity',
    
    # Temporal
    'TemporalDiffEngine',
    'get_temporal_engine',
    'ExtractionRecord',
    'ExtractionStatus',
    'TemporalPair',
    
    # Frontier
    'compute_frontier',
    'compute_multi_frontier',
    'FrontierChart',
    'FrontierPoint',
    
    # Database
    'init_phase2_schema',
    'save_snapshot',
    'get_snapshot',
    'get_latest_snapshots',
    'save_extraction_record',
    'get_extraction_history',
    'save_regression_event',
    'get_regression_history',
    'save_prs_record',
    'get_prs_history',
]

