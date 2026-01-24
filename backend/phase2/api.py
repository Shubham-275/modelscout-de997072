

from flask import Blueprint, request, jsonify, Response, stream_with_context
from datetime import datetime
import sqlite3
import json
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


# =============================================================================
# MODELSCOUT ANALYST ENDPOINTS (PHASE 2)
# =============================================================================

try:
    from .model_scout_analyst import (
        get_model_scout_analyst,
        UserRequirements,
        refresh_analyst
    )
    ANALYST_AVAILABLE = True
    print("[OK] ModelScout Analyst module loaded successfully")
except ImportError as e:
    ANALYST_AVAILABLE = False
    print(f"[WARN] ModelScout Analyst import failed: {e}")
except Exception as e:
    ANALYST_AVAILABLE = False
    print(f"[ERROR] ModelScout Analyst unexpected error: {e}")
    import traceback
    traceback.print_exc()


# Import Mino-powered analyst
try:
    from .mino_analyst import get_mino_analyst
    MINO_ANALYST_AVAILABLE = True
    print("[OK] Mino AI Analyst loaded successfully")
except ImportError as e:
    MINO_ANALYST_AVAILABLE = False
    print(f"[WARN] Mino Analyst import failed: {e}")
except Exception as e:
    MINO_ANALYST_AVAILABLE = False
    print(f"[ERROR] Mino Analyst error: {e}")


# Import Multimodal Analyst
try:
    from .multimodal_analyst import MultimodalAnalyst, MultimodalRequirements
    MULTIMODAL_ANALYST_AVAILABLE = True
    print("[OK] Multimodal Analyst loaded successfully")
except ImportError as e:
    MULTIMODAL_ANALYST_AVAILABLE = False
    print(f"[WARN] Multimodal Analyst import failed: {e}")
except Exception as e:
    MULTIMODAL_ANALYST_AVAILABLE = False
    print(f"[ERROR] Multimodal Analyst error: {e}")


@phase2_api.route('/analyst/recommend', methods=['POST'])
def analyst_recommend():
    """
    Get a model recommendation based on user requirements.
    
    Request body:
    {
        "use_case": "Building a code assistant for developers",
        "priorities": {
            "cost": "low",
            "quality": "high",
            "latency": "medium",
            "context_length": "medium"
        },
        "monthly_budget_usd": 100,
        "expected_tokens_per_month": 5000000
    }
    
    Response:
    - Primary Recommendation with reasoning
    - Why other models were not chosen
    - Cost estimate with assumptions
    - Important caveats
    - Data freshness warning
    """
    if not ANALYST_AVAILABLE:
        return jsonify({"error": "Analyst module not available"}), 500
    
    data = request.get_json() or {}
    
    # Validate required fields
    if not data.get("use_case"):
        return jsonify({
            "error": "Missing required field: use_case",
            "example": {
                "use_case": "Building a chatbot for customer support",
                "priorities": {
                    "cost": "medium",
                    "quality": "high",
                    "latency": "low",
                    "context_length": "short"
                },
                "monthly_budget_usd": 500,
                "expected_tokens_per_month": 10000000
            }
        }), 400
    
    try:
        requirements = UserRequirements.from_dict(data)
        analyst = get_model_scout_analyst()
        analyst.refresh_data() # Ensure we use the latest DB data
        recommendation = analyst.recommend(requirements)
        
        return jsonify({
            "status": "success",
            "recommendation": recommendation.to_dict(),
            "user_requirements": requirements.to_dict(),
            "_meta": {
                "note": "This recommendation is based on benchmark data and stated requirements. Always validate against your specific use case.",
                "documentation": "/api/v2/docs/analyst"
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Failed to generate recommendation",
            "message": str(e)
        }), 500


@phase2_api.route('/analyst/benchmarks', methods=['POST'])
def analyst_benchmarks():
    """
    Generate detailed benchmark report via Mino AI.
    
    Request body:
    {
        "model_name": "DeepSeek R1"
    }
    """
    # Check availability (re-using the check from recommend_ai if possible, or assuming imports exist)
    if not MINO_ANALYST_AVAILABLE:
        return jsonify({"error": "Mino Analyst module not available"}), 503
        
    data = request.get_json() or {}
    model_name = data.get("model_name", "DeepSeek R1")
    
    try:
        analyst = get_mino_analyst()
        result = analyst.generate_benchmark_report(model_name)
        
        return jsonify({
            "status": "success",
            "powered_by": "Mino AI",
            "report": result
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Failed to generate benchmark report",
            "message": str(e)
        }), 500


@phase2_api.route('/analyst/benchmarks/stream', methods=['POST'])
def analyst_benchmarks_stream():
    """Streaming endpoint for benchmark deep dive."""
    data = request.json
    if not data or 'model_name' not in data:
        return jsonify({"error": "Missing model_name"}), 400
        
    model_name = data.get('model_name')
    analyst = get_mino_analyst()
    
    def generate():
        for event in analyst.generate_benchmark_report_stream(model_name):
            yield f"data: {json.dumps(event)}\n\n"
    
    return Response(stream_with_context(generate()), content_type='text/event-stream')

# Make sure this route is registered!
@phase2_api.route('/analyst/recommend/ai', methods=['POST'])
def analyst_recommend_ai():
    """
    Get an AI-powered model recommendation using Gemini.
    
    This endpoint uses Gemini AI to analyze user requirements and 
    recommend from ALL available models (not a fixed list).
    
    Request body:
    {
        "use_case": "Building a chatbot for customer support",
        "priorities": {
            "cost": "low|medium|high",
            "quality": "low|medium|high", 
            "latency": "low|medium|high",
            "context_length": "short|medium|long"
        },
        "monthly_budget_usd": 100,
        "expected_tokens_per_month": 5000000
    }
    
    Returns:
    - Recommended model with confidence score
    - Cost per 1K tokens (input and output)
    - Model strengths and weaknesses
    - Why it's better than alternatives
    - Number of models analyzed
    """
    if not MINO_ANALYST_AVAILABLE:
        return jsonify({
            "error": "Mino AI Analyst not available",
            "message": "Mino API configuration missing. Check MINO_API_KEY in .env"
        }), 503
    
    data = request.get_json()
    if not data:
        return jsonify({
            "error": "Missing request body",
            "example": {
                "use_case": "Describe what you want to build",
                "priorities": {
                    "cost": "low",
                    "quality": "high",
                    "latency": "medium",
                    "context_length": "medium"
                },
                "monthly_budget_usd": 100,
                "expected_tokens_per_month": 5000000
            }
        }), 400
    
    try:
        analyst = get_mino_analyst()
        
        def generate():
            try:
                # Initial log
                yield f"data: {json.dumps({'type': 'log', 'message': 'Initializing Phase 2 Analyst...'})}\n\n"
                
                stream = analyst.recommend_stream(
                    use_case=data.get("use_case", "General AI assistant"),
                    priorities=data.get("priorities", {}),
                    monthly_budget_usd=data.get("monthly_budget_usd"),
                    expected_tokens_per_month=data.get("expected_tokens_per_month")
                )
                
                for event in stream:
                    # Format as SSE
                    yield f"data: {json.dumps(event)}\n\n"
                    
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "AI recommendation failed",
            "message": str(e)
        }), 500


@phase2_api.route('/analyst/disqualify/<model_id>', methods=['POST'])
def analyst_disqualify(model_id: str):
    """
    Explain why a specific model is not recommended for given requirements.
    
    "Why NOT This Model?" Disqualifier Mode
    
    Request body: Same as /analyst/recommend
    
    Response:
    - Whether model is recommended
    - Disqualification reasons
    - Requirement mismatches with details
    - Alternative suggestion
    """
    if not ANALYST_AVAILABLE:
        return jsonify({"error": "Analyst module not available"}), 500
    
    data = request.get_json() or {}
    
    try:
        requirements = UserRequirements.from_dict(data)
        analyst = get_model_scout_analyst()
        analyst.refresh_data()
        result = analyst.explain_disqualification(model_id, requirements)
        
        return jsonify({
            "status": "success",
            "disqualification_analysis": result.to_dict(),
            "user_requirements": requirements.to_dict(),
            "_meta": {
                "note": "This analysis explains requirement mismatches. A model may still work for your use case despite mismatches."
            }
        })
    except Exception as e:
        return jsonify({
            "error": "Failed to analyze disqualification",
            "message": str(e)
        }), 500


@phase2_api.route('/analyst/compare', methods=['POST'])
def analyst_compare():
    """
    Compare two models side-by-side.
    
    Request body:
    {
        "model_a": "gpt-4o",
        "model_b": "claude-3.5-sonnet"
    }
    
    Response:
    - High-level verdict
    - Strengths of each model
    - Key tradeoffs
    - Which user should choose which
    - Benchmark deltas
    - Cost comparison
    """
    if not ANALYST_AVAILABLE:
        return jsonify({"error": "Analyst module not available"}), 500
    
    data = request.get_json() or {}
    
    model_a = data.get("model_a")
    model_b = data.get("model_b")
    
    if not model_a or not model_b:
        return jsonify({
            "error": "Both model_a and model_b are required",
            "example": {
                "model_a": "gpt-4o",
                "model_b": "claude-3.5-sonnet"
            }
        }), 400
    
    try:
        # Optional: include requirements for context
        requirements = None
        if data.get("requirements"):
            requirements = UserRequirements.from_dict(data["requirements"])
        
        analyst = get_model_scout_analyst()
        analyst.refresh_data()
        comparison = analyst.compare(model_a, model_b, requirements)
        
        return jsonify({
            "status": "success",
            "comparison": comparison.to_dict(),
            "_meta": {
                "note": "No winner is declared unless context clearly favors one model. Consider your specific requirements.",
                "sources": "Arena ELO, MMLU, HumanEval, pricing data"
            }
        })
    except Exception as e:
        return jsonify({
            "error": "Failed to compare models",
            "message": str(e)
        }), 500


@phase2_api.route('/analyst/cost/<model_id>', methods=['GET'])
def analyst_cost_breakdown(model_id: str):
    """
    Get detailed cost breakdown for a model.
    
    Query params:
    - monthly_tokens: Expected monthly token usage (default: 1000000)
    - input_ratio: Ratio of input to total tokens (default: 0.75)
    
    Response includes:
    - Detailed cost estimate with all assumptions
    - Unit prices
    - Usage tiers (1M, 10M, 100M tokens)
    """
    if not ANALYST_AVAILABLE:
        return jsonify({"error": "Analyst module not available"}), 500
    
    monthly_tokens = request.args.get("monthly_tokens", 1000000, type=int)
    input_ratio = request.args.get("input_ratio", 0.75, type=float)
    
    try:
        analyst = get_model_scout_analyst()
        breakdown = analyst.get_cost_breakdown(model_id, monthly_tokens, input_ratio)
        
        return jsonify({
            "status": "success" if "error" not in breakdown else "error",
            **breakdown,
            "_meta": {
                "note": "Cost estimates are based on published API pricing. Actual costs may vary."
            }
        })
    except Exception as e:
        return jsonify({
            "error": "Failed to calculate cost",
            "message": str(e)
        }), 500


@phase2_api.route('/analyst/data-status', methods=['GET'])
def analyst_data_status():
    """
    Get current data status and freshness.
    
    Returns:
    - Data freshness statement
    - Benchmark snapshot date
    - Models tracked
    - Data completeness with warnings
    """
    if not ANALYST_AVAILABLE:
        return jsonify({"error": "Analyst module not available"}), 500
    
    try:
        analyst = get_model_scout_analyst()
        status = analyst.get_data_status()
        
        return jsonify({
            "status": "success",
            **status,
            "_meta": {
                "note": "Data warnings indicate incomplete benchmark coverage. Results may be less reliable for models with warnings."
            }
        })
    except Exception as e:
        return jsonify({
            "error": "Failed to get data status",
            "message": str(e)
        }), 500


@phase2_api.route('/analyst/models', methods=['GET'])
def analyst_list_models():
    """
    List all models available for analysis.
    
    Returns available models with basic info.
    """
    if not ANALYST_AVAILABLE:
        return jsonify({"error": "Analyst module not available"}), 500
    
    try:
        analyst = get_model_scout_analyst()
        
        models = []
        for model_id, benchmarks in analyst.benchmark_data.items():
            pricing = analyst.pricing_data.get(model_id, {})
            models.append({
                "model_id": model_id,
                "provider": pricing.get("provider", "Unknown"),
                "arena_elo": benchmarks.get("arena_elo"),
                "context_window": benchmarks.get("context_window"),
                "pricing": {
                    "input_per_1m": pricing.get("input", 0),
                    "output_per_1m": pricing.get("output", 0)
                }
            })
        
        # Sort by Arena ELO descending
        models.sort(key=lambda x: x.get("arena_elo") or 0, reverse=True)
        
        return jsonify({
            "status": "success",
            "models": models,
            "total": len(models),
            "data_freshness": analyst._get_data_freshness()
        })
    except Exception as e:
        return jsonify({
            "error": "Failed to list models",
            "message": str(e)
        }), 500


@phase2_api.route('/docs/analyst', methods=['GET'])
def analyst_documentation():
    """
    ModelScout Analyst documentation.
    """
    return jsonify({
        "name": "ModelScout AI Analyst",
        "version": "Phase 2",
        "mission": "Help users make confident model decisions by understanding tradeoffs, not by chasing rankings.",
        "endpoints": {
            "/api/v2/analyst/recommend": {
                "method": "POST",
                "description": "Get a model recommendation based on user requirements",
                "body": {
                    "use_case": "string (required)",
                    "priorities": {
                        "cost": "low | medium | high",
                        "quality": "low | medium | high",
                        "latency": "low | medium | high",
                        "context_length": "short | medium | long"
                    },
                    "monthly_budget_usd": "number (optional)",
                    "expected_tokens_per_month": "number (optional)"
                }
            },
            "/api/v2/analyst/disqualify/<model_id>": {
                "method": "POST",
                "description": "Explain why a specific model is not recommended",
                "body": "Same as /recommend"
            },
            "/api/v2/analyst/compare": {
                "method": "POST",
                "description": "Compare two models side-by-side",
                "body": {
                    "model_a": "string (required)",
                    "model_b": "string (required)"
                }
            },
            "/api/v2/analyst/cost/<model_id>": {
                "method": "GET",
                "description": "Get detailed cost breakdown",
                "params": {
                    "monthly_tokens": "int (default: 1000000)",
                    "input_ratio": "float (default: 0.75)"
                }
            },
            "/api/v2/analyst/data-status": {
                "method": "GET",
                "description": "Get data freshness and completeness status"
            },
            "/api/v2/analyst/models": {
                "method": "GET",
                "description": "List all available models"
            }
        },
        "principles": [
            "Never say 'best model overall'",
            "Always mention cost vs quality tradeoff",
            "Always include data freshness",
            "Cost estimates always include assumptions",
            "Be direct but neutral in disqualifications"
        ],
        "tone": "Clear, concise, professional. No emojis. No marketing language. No absolutes."
    })


@phase2_api.route('/analyst/recommend/multimodal', methods=['POST'])
def analyst_recommend_multimodal():
    """
    Get a multimodal model recommendation (voice, video, image, 3D).
    
    This endpoint supports ALL model types beyond text LLMs.
    
    Request body:
    {
        "use_case": "Generate product images for e-commerce",
        "modality": "image|video|voice|3d",
        "priorities": {
            "quality": "low|medium|high",
            "cost": "low|medium|high",
            "speed": "low|medium|high"
        },
        "monthly_budget_usd": 100,
        "expected_usage_per_month": 1000,  # images, seconds, characters, or models
        
        # Modality-specific requirements (optional)
        "image_requirements": {
            "min_resolution": 1024,
            "needs_safety_filter": true,
            "needs_style_diversity": true
        },
        "video_requirements": {
            "min_duration_sec": 10,
            "min_resolution": "1080p"
        },
        "voice_requirements": {
            "needs_voice_cloning": true,
            "languages": ["en", "es", "fr"],
            "needs_emotions": true
        },
        "three_d_requirements": {
            "needs_rigging": true,
            "min_polygons": 50000,
            "needs_optimization": true
        }
    }
    
    Returns:
    - Recommended model with reasoning
    - Modality-specific benchmarks
    - Cost breakdown
    - Alternative models
    - Confidence score
    """
    if not MULTIMODAL_ANALYST_AVAILABLE:
        return jsonify({
            "error": "Multimodal Analyst not available",
            "message": "Multimodal analyst module failed to load"
        }), 503
    
    data = request.get_json()
    if not data:
        return jsonify({
            "error": "Missing request body",
            "example": {
                "use_case": "Generate product images for e-commerce",
                "modality": "image",
                "priorities": {
                    "quality": "high",
                    "cost": "medium",
                    "speed": "high"
                },
                "monthly_budget_usd": 100,
                "expected_usage_per_month": 1000,
                "image_requirements": {
                    "min_resolution": 1024,
                    "needs_safety_filter": True
                }
            }
        }), 400
    
    # Validate modality
    modality = data.get("modality", "").lower()
    if modality not in ["image", "video", "voice", "3d"]:
        return jsonify({
            "error": "Invalid modality",
            "message": f"Modality must be one of: image, video, voice, 3d. Got: {modality}",
            "supported_modalities": ["image", "video", "voice", "3d"]
        }), 400
    
    try:
        requirements = MultimodalRequirements.from_dict(data)
        analyst = MultimodalAnalyst()
        recommendation = analyst.recommend(requirements)
        
        return jsonify({
            "status": "success",
            "modality": modality,
            "recommendation": recommendation,
            "user_requirements": {
                "use_case": data.get("use_case"),
                "modality": modality,
                "priorities": data.get("priorities"),
                "monthly_budget_usd": data.get("monthly_budget_usd"),
                "expected_usage_per_month": data.get("expected_usage_per_month")
            },
            "_meta": {
                "note": "This recommendation is based on modality-specific benchmarks and your stated requirements.",
                "supported_modalities": analyst.get_supported_modalities(),
                "documentation": "/api/v2/docs/multimodal"
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Failed to generate multimodal recommendation",
            "message": str(e)
        }), 500


@phase2_api.route('/analyst/models/multimodal', methods=['GET'])
def get_multimodal_models():
    """
    Get all available multimodal models by modality.
    
    Query params:
    - modality: Filter by modality (image, video, voice, 3d)
    
    Returns:
    - List of models with their benchmarks and pricing
    """
    if not MULTIMODAL_ANALYST_AVAILABLE:
        return jsonify({
            "error": "Multimodal Analyst not available"
        }), 503
    
    modality = request.args.get('modality', '').lower()
    
    try:
        analyst = MultimodalAnalyst()
        
        if modality:
            if modality not in ["image", "video", "voice", "3d"]:
                return jsonify({
                    "error": "Invalid modality",
                    "supported": analyst.get_supported_modalities()
                }), 400
            
            models = analyst.get_models_by_modality(modality)
            model_data = {
                model_id: {
                    "benchmarks": analyst.benchmark_data.get(model_id, {}),
                    "pricing": analyst.pricing_data.get(model_id, {})
                }
                for model_id in models
            }
            
            return jsonify({
                "modality": modality,
                "models": model_data,
                "count": len(models)
            })
        else:
            # Return all modalities
            all_modalities = analyst.get_supported_modalities()
            result = {}
            
            for mod in all_modalities:
                models = analyst.get_models_by_modality(mod)
                result[mod] = {
                    "count": len(models),
                    "models": models
                }
            
            return jsonify({
                "supported_modalities": all_modalities,
                "models_by_modality": result
            })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Failed to retrieve multimodal models",
            "message": str(e)
        }), 500


@phase2_api.route('/docs/multimodal', methods=['GET'])
def multimodal_documentation():
    """
    Multimodal analyst documentation.
    """
    return jsonify({
        "name": "Multimodal AI Model Analyst",
        "description": "Recommendation engine for voice, video, image, and 3D generation models",
        "supported_modalities": {
            "image": {
                "metrics": [
                    "image_quality_score (0-100)",
                    "prompt_adherence (0-100)",
                    "style_diversity (0-100)",
                    "resolution_max (pixels)",
                    "generation_time_sec",
                    "nsfw_filter (boolean)"
                ],
                "example_models": ["dall-e-3", "stable-diffusion-xl", "midjourney-v6", "imagen-2"]
            },
            "video": {
                "metrics": [
                    "video_quality_score (0-100)",
                    "temporal_consistency (0-100)",
                    "motion_realism (0-100)",
                    "max_duration_sec",
                    "resolution",
                    "fps"
                ],
                "example_models": ["runway-gen-2", "pika-1.0", "stable-video-diffusion", "sora"]
            },
            "voice": {
                "metrics": [
                    "voice_naturalness (0-100)",
                    "emotion_range (0-100)",
                    "language_support (count)",
                    "latency_ms",
                    "voice_cloning (boolean)"
                ],
                "example_models": ["elevenlabs-turbo", "elevenlabs-multilingual", "openai-tts-1", "openai-tts-1-hd"]
            },
            "3d": {
                "metrics": [
                    "mesh_quality_score (0-100)",
                    "texture_quality (0-100)",
                    "polygon_efficiency (0-100)",
                    "generation_time_sec",
                    "max_polygons",
                    "supports_rigging (boolean)"
                ],
                "example_models": ["meshy-3", "luma-genie", "spline-ai", "point-e"]
            }
        },
        "scoring_approach": "Dynamic, modality-specific scoring based on user requirements. No fixed combinations.",
        "principles": [
            "Each modality has unique metrics and scoring logic",
            "Recommendations are based on actual benchmarks, not marketing claims",
            "Cost transparency with detailed breakdowns",
            "Quality vs cost tradeoffs clearly explained",
            "Supports unlimited model combinations"
        ],
        "endpoints": {
            "/api/v2/analyst/recommend/multimodal": "Get recommendation for voice/video/image/3D models",
            "/api/v2/analyst/models/multimodal": "List all multimodal models by modality"
        }
    })

