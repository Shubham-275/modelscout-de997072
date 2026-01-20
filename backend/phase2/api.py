"""
Model Scout - Phase 2 API Endpoints

PHASE 2 ENDPOINTS:
- /api/v2/prs/<model_id> - Compute and return PRS with full breakdown
- /api/v2/snapshots - Snapshot management
- /api/v2/snapshots/<snapshot_id>/diff - Temporal diff
- /api/v2/regressions - Regression detection and history
- /api/v2/frontier - Cost-performance frontier

DATA TRANSPARENCY GUARANTEES:
- Raw benchmark values always accessible
- Composite scores never hide inputs
- Hover/tooltips must expose formulas
- PRS explicitly labeled as non-ranking
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import sqlite3
import os

from .prs import compute_prs, PRSComponents
from .snapshots import (
    Snapshot, 
    BenchmarkVersion, 
    create_snapshot, 
    verify_snapshot, 
    diff_snapshots
)
from .regression import detect_regressions, RegressionThresholds
from .temporal import get_temporal_engine
from .frontier import compute_frontier, compute_multi_frontier
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

# Create blueprint
phase2_api = Blueprint('phase2', __name__, url_prefix='/api/v2')

# Database path
DATABASE_PATH = os.environ.get('DATABASE_PATH', './modelscout.db')


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@phase2_api.before_request
def ensure_schema():
    """Ensure Phase 2 schema exists."""
    conn = get_db()
    init_phase2_schema(conn)
    conn.close()


# =============================================================================
# PRS ENDPOINTS
# =============================================================================

@phase2_api.route('/prs/<model_id>', methods=['GET'])
def get_model_prs(model_id: str):
    """
    Compute Performance Reliability Score for a model.
    
    PRS is a NON-RANKING metric. It does not imply preference.
    
    Query params:
    - snapshot_id: Optional specific snapshot (defaults to latest)
    - include_history: Include PRS history (default: false)
    
    Returns:
        Full PRS breakdown with audit trail
    """
    snapshot_id = request.args.get('snapshot_id')
    include_history = request.args.get('include_history', 'false').lower() == 'true'
    
    conn = get_db()
    
    try:
        # Get snapshot data
        if snapshot_id:
            snapshot_data = get_snapshot(conn, snapshot_id)
        else:
            snapshots = get_latest_snapshots(conn, 2)
            snapshot_data = snapshots[0] if snapshots else None
        
        if not snapshot_data:
            return jsonify({
                "error": "No snapshot available",
                "message": "Please run an extraction first"
            }), 404
        
        # Get model scores from snapshot
        model_scores = snapshot_data.get("model_scores", {})
        current_scores = model_scores.get(model_id)
        
        if not current_scores:
            return jsonify({
                "error": "Model not found in snapshot",
                "model_id": model_id,
                "available_models": list(model_scores.keys())
            }), 404
        
        # Get extraction history for stability calculation
        extraction_history = []
        expected_benchmarks = list(current_scores.keys())
        
        # Get previous snapshot for temporal reliability
        snapshots = get_latest_snapshots(conn, 2)
        previous_scores = None
        previous_benchmarks = None
        
        if len(snapshots) > 1:
            prev_snapshot = snapshots[1]
            prev_model_scores = prev_snapshot.get("model_scores", {})
            previous_scores = prev_model_scores.get(model_id)
            if previous_scores:
                previous_benchmarks = list(previous_scores.keys())
        
        # Compute PRS
        prs = compute_prs(
            model_id=model_id,
            current_scores=current_scores,
            all_model_scores=model_scores,
            extraction_history=extraction_history,
            expected_benchmarks=expected_benchmarks,
            previous_scores=previous_scores,
            previous_benchmarks=previous_benchmarks
        )
        
        # Save PRS record
        save_prs_record(conn, {
            "model_id": model_id,
            "snapshot_id": snapshot_data["snapshot_id"],
            "final_prs": prs.final_prs,
            "capability_consistency": prs.capability_consistency,
            "benchmark_stability": prs.benchmark_stability,
            "temporal_reliability": prs.temporal_reliability,
            "benchmarks_included": prs.benchmarks_included,
            "missing_benchmarks": prs.missing_benchmarks,
            "extraction_count": prs.extraction_count,
            "computation_timestamp": prs.computation_timestamp
        })
        
        response = {
            "model_id": model_id,
            "prs": prs.to_dict(),
            "snapshot_id": snapshot_data["snapshot_id"],
            "raw_scores": current_scores,  # DATA TRANSPARENCY: Raw values always accessible
            "_meta": {
                "note": "PRS is a NON-RANKING stability metric",
                "documentation": "/api/v2/docs/prs"
            }
        }
        
        # Include history if requested
        if include_history:
            response["history"] = get_prs_history(conn, model_id, limit=10)
        
        return jsonify(response)
    
    finally:
        conn.close()


# =============================================================================
# SNAPSHOT ENDPOINTS
# =============================================================================

@phase2_api.route('/snapshots', methods=['GET'])
def list_snapshots():
    """
    List available snapshots.
    
    Query params:
    - limit: Max snapshots to return (default: 10)
    """
    limit = int(request.args.get('limit', 10))
    
    conn = get_db()
    try:
        snapshots = get_latest_snapshots(conn, limit)
        
        return jsonify({
            "snapshots": [
                {
                    "snapshot_id": s["snapshot_id"],
                    "timestamp_utc": s["timestamp_utc"],
                    "content_hash": s["content_hash"][:16] + "...",
                    "model_count": len(s["model_ids"]),
                    "models": s["model_ids"]
                }
                for s in snapshots
            ],
            "total": len(snapshots)
        })
    finally:
        conn.close()


@phase2_api.route('/snapshots/<snapshot_id>', methods=['GET'])
def get_snapshot_detail(snapshot_id: str):
    """
    Get detailed snapshot data.
    
    Includes full model scores for transparency.
    """
    conn = get_db()
    try:
        snapshot = get_snapshot(conn, snapshot_id)
        
        if not snapshot:
            return jsonify({"error": "Snapshot not found"}), 404
        
        return jsonify({
            "snapshot": snapshot,
            "integrity_check": {
                "stored_hash": snapshot["content_hash"],
                "note": "Use /api/v2/snapshots/<id>/verify for full verification"
            }
        })
    finally:
        conn.close()


@phase2_api.route('/snapshots/<snapshot_id>/verify', methods=['GET'])
def verify_snapshot_integrity(snapshot_id: str):
    """
    Verify snapshot integrity.
    
    Recomputes hash and compares to stored value.
    """
    conn = get_db()
    try:
        snapshot_data = get_snapshot(conn, snapshot_id)
        
        if not snapshot_data:
            return jsonify({"error": "Snapshot not found"}), 404
        
        # Reconstruct Snapshot object
        benchmark_versions = [
            BenchmarkVersion(**bv) for bv in snapshot_data.get("benchmark_versions", [])
        ]
        
        snapshot = Snapshot(
            snapshot_id=snapshot_data["snapshot_id"],
            timestamp_utc=snapshot_data["timestamp_utc"],
            model_ids=snapshot_data["model_ids"],
            model_scores=snapshot_data["model_scores"],
            benchmark_versions=benchmark_versions,
            weights_used=snapshot_data.get("weights_used", {}),
            content_hash=snapshot_data["content_hash"]
        )
        
        is_valid, message = verify_snapshot(snapshot)
        
        return jsonify({
            "snapshot_id": snapshot_id,
            "integrity_valid": is_valid,
            "message": message,
            "stored_hash": snapshot_data["content_hash"],
            "computed_hash": snapshot._compute_hash()
        })
    finally:
        conn.close()


@phase2_api.route('/snapshots/diff', methods=['GET'])
def diff_latest_snapshots():
    """
    Diff the two most recent snapshots.
    
    STRICT SEMANTICS:
    - Only compares if benchmark versions match
    - Returns "Incomparable" if versions differ
    """
    conn = get_db()
    try:
        snapshots = get_latest_snapshots(conn, 2)
        
        if len(snapshots) < 1:
            return jsonify({"error": "No snapshots available"}), 404
        
        if len(snapshots) < 2:
            return jsonify({
                "status": "no_previous_snapshot",
                "message": "Only one snapshot available. Cannot compute diff.",
                "current_snapshot_id": snapshots[0]["snapshot_id"]
            })
        
        # Reconstruct Snapshot objects
        def to_snapshot(data):
            benchmark_versions = [
                BenchmarkVersion(**bv) for bv in data.get("benchmark_versions", [])
            ]
            return Snapshot(
                snapshot_id=data["snapshot_id"],
                timestamp_utc=data["timestamp_utc"],
                model_ids=data["model_ids"],
                model_scores=data["model_scores"],
                benchmark_versions=benchmark_versions,
                weights_used=data.get("weights_used", {}),
                content_hash=data["content_hash"]
            )
        
        current = to_snapshot(snapshots[0])
        previous = to_snapshot(snapshots[1])
        
        diff = diff_snapshots(current, previous)
        
        return jsonify(diff.to_dict())
    finally:
        conn.close()


# =============================================================================
# REGRESSION ENDPOINTS
# =============================================================================

@phase2_api.route('/regressions/detect/<model_id>', methods=['POST'])
def detect_model_regressions(model_id: str):
    """
    Detect regressions for a model between snapshots.
    
    Request body (optional):
    {
        "thresholds": {
            "minor_threshold_pct": 5.0,
            "major_threshold_pct": 10.0
        }
    }
    
    UI REQUIREMENTS:
    - Shows exact delta %
    - Shows benchmark source
    - Shows snapshot IDs used
    """
    conn = get_db()
    
    try:
        # Get threshold config from request
        config = request.get_json() or {}
        threshold_config = config.get("thresholds", {})
        
        thresholds = RegressionThresholds(
            minor_threshold_pct=threshold_config.get("minor_threshold_pct", 5.0),
            major_threshold_pct=threshold_config.get("major_threshold_pct", 10.0)
        )
        
        # Get latest two snapshots
        snapshots = get_latest_snapshots(conn, 2)
        
        if len(snapshots) < 2:
            return jsonify({
                "error": "Insufficient snapshots for regression detection",
                "message": "Need at least 2 snapshots to detect regressions"
            }), 400
        
        current_snapshot = snapshots[0]
        previous_snapshot = snapshots[1]
        
        # Get scores
        current_scores = current_snapshot["model_scores"].get(model_id, {})
        previous_scores = previous_snapshot["model_scores"].get(model_id, {})
        
        if not current_scores:
            return jsonify({
                "error": "Model not found in current snapshot",
                "model_id": model_id
            }), 404
        
        if not previous_scores:
            return jsonify({
                "error": "Model not found in previous snapshot",
                "model_id": model_id,
                "message": "Cannot compute regression without baseline"
            }), 404
        
        # Detect regressions
        report = detect_regressions(
            model_id=model_id,
            current_scores=current_scores,
            previous_scores=previous_scores,
            current_snapshot_id=current_snapshot["snapshot_id"],
            previous_snapshot_id=previous_snapshot["snapshot_id"],
            thresholds=thresholds
        )
        
        # Save regression events to audit trail
        for event in report.events:
            if event.severity.value != "none":
                save_regression_event(conn, {
                    "model_id": event.model_id,
                    "benchmark_id": event.benchmark_id,
                    "benchmark_category": event.benchmark_category,
                    "current_score": event.current_score,
                    "previous_score": event.previous_score,
                    "delta_absolute": event.delta_absolute,
                    "delta_percentage": event.delta_percentage,
                    "severity": event.severity.value,
                    "thresholds_used": event.thresholds_used,
                    "current_snapshot_id": event.current_snapshot_id,
                    "previous_snapshot_id": event.previous_snapshot_id,
                    "detected_at": event.detected_at
                })
        
        return jsonify(report.to_dict())
    
    finally:
        conn.close()


@phase2_api.route('/regressions/history', methods=['GET'])
def get_regression_history_api():
    """
    Get regression history.
    
    Query params:
    - model_id: Filter by model
    - severity: Filter by severity (minor/major)
    - limit: Max results (default: 50)
    """
    model_id = request.args.get('model_id')
    severity = request.args.get('severity')
    limit = int(request.args.get('limit', 50))
    
    conn = get_db()
    try:
        history = get_regression_history(conn, model_id, severity, limit)
        
        return jsonify({
            "regressions": history,
            "total": len(history),
            "filters": {
                "model_id": model_id,
                "severity": severity
            }
        })
    finally:
        conn.close()


# =============================================================================
# FRONTIER ENDPOINTS
# =============================================================================

@phase2_api.route('/frontier', methods=['GET'])
def get_frontier():
    """
    Compute cost-performance frontier.
    
    Query params:
    - cost_metric: Cost metric (default: input_price)
    - capability_metric: Capability metric (default: average_score)
    - models: Comma-separated model IDs to include (default: all)
    
    MANDATORY DISCLOSURES:
    - Normalization scope is the filtered model set
    - Frontier does not imply recommendation
    """
    cost_metric = request.args.get('cost_metric', 'input_price')
    capability_metric = request.args.get('capability_metric', 'average_score')
    models_filter = request.args.get('models')
    
    conn = get_db()
    try:
        # Get latest snapshot
        snapshots = get_latest_snapshots(conn, 1)
        
        if not snapshots:
            return jsonify({"error": "No snapshots available"}), 404
        
        snapshot = snapshots[0]
        model_scores = snapshot["model_scores"]
        
        # Apply filter if specified
        if models_filter:
            filter_list = [m.strip() for m in models_filter.split(',')]
            model_scores = {k: v for k, v in model_scores.items() if k in filter_list}
            filter_description = f"Filtered: {len(filter_list)} models"
        else:
            filter_description = f"All models ({len(model_scores)} in snapshot)"
        
        # Compute frontier
        frontier = compute_frontier(
            model_data=model_scores,
            cost_metric=cost_metric,
            capability_metric=capability_metric,
            filter_description=filter_description
        )
        
        response = frontier.to_dict()
        response["snapshot_id"] = snapshot["snapshot_id"]
        response["raw_data"] = model_scores  # DATA TRANSPARENCY
        
        return jsonify(response)
    
    finally:
        conn.close()


@phase2_api.route('/frontier/multi', methods=['GET'])
def get_multi_frontier():
    """
    Compute multiple frontier combinations.
    
    Returns frontiers for all cost × capability metric combinations.
    """
    conn = get_db()
    try:
        snapshots = get_latest_snapshots(conn, 1)
        
        if not snapshots:
            return jsonify({"error": "No snapshots available"}), 404
        
        snapshot = snapshots[0]
        model_scores = snapshot["model_scores"]
        
        frontiers = compute_multi_frontier(
            model_data=model_scores,
            filter_description=f"All models ({len(model_scores)})"
        )
        
        return jsonify({
            "frontiers": {k: v.to_dict() for k, v in frontiers.items()},
            "snapshot_id": snapshot["snapshot_id"]
        })
    
    finally:
        conn.close()


# =============================================================================
# DOCUMENTATION ENDPOINT
# =============================================================================

@phase2_api.route('/docs/prs', methods=['GET'])
def prs_documentation():
    """
    PRS documentation for transparency.
    """
    return jsonify({
        "name": "Performance Reliability Score (PRS)",
        "type": "NON-RANKING composite reliability metric",
        "range": "[0, 100]",
        "formula": "PRS = (0.40 × CapabilityConsistency) + (0.35 × BenchmarkStability) + (0.25 × TemporalReliability)",
        "components": {
            "capability_consistency": {
                "weight": 0.40,
                "definition": "Normalized mean benchmark score across all included benchmarks",
                "normalization": "Snapshot-local (only models present in the current snapshot)"
            },
            "benchmark_stability": {
                "weight": 0.35,
                "definition": "Inverse normalized variance of scores across last N extractions",
                "N": 3,
                "missing_data_penalty": "15% multiplicative penalty per missing benchmark"
            },
            "temporal_reliability": {
                "weight": 0.25,
                "definition": "Penalizes sudden score volatility and benchmark appearance/disappearance",
                "volatility_thresholds": {
                    "0-5%": "No penalty",
                    "5-20%": "Linear penalty up to 30%",
                    ">20%": "Severe penalty (capped at 70%)"
                }
            }
        },
        "hard_rules": [
            "PRS must NOT change model ordering",
            "PRS must NOT be used as a leaderboard",
            "Raw benchmark values MUST always be accessible"
        ],
        "disclaimer": "PRS is a stability and trust signal only. It does not imply model preference or quality ranking."
    })
