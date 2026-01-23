"""
Model Scout - Flask API Server (Phase 1)
Main orchestration layer connecting frontend to Mino agents

PHASE 1 REQUIREMENTS:
- SSE (text/event-stream) live logs
- Keepalive comments every 10 seconds
- Close streams deterministically on completion or failure
"""
import os
import json
import time
import threading
from queue import Queue, Empty
from flask import Flask, Response, request, jsonify, stream_with_context
from flask_cors import CORS
from datetime import datetime

from config import BENCHMARK_SOURCES, SSE_KEEPALIVE_INTERVAL
from workers import parallel_snipe, parallel_compare
from database import get_model_history, get_cached_result, get_connection

app = Flask(__name__)

# SECURE CORS Configuration - Environment-based
# Development: Allow localhost origins
# Production: Only allow explicitly configured origins
if os.environ.get("FLASK_ENV") == "development":
    # Development mode - allow common dev ports
    allowed_origins = [
        "http://localhost:8080",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    CORS(app, origins=allowed_origins, supports_credentials=True)
else:
    # Production mode - only allow configured origins
    allowed_origins_str = os.environ.get("ALLOWED_ORIGINS", "")
    if allowed_origins_str:
        allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]
        CORS(app, origins=allowed_origins, supports_credentials=True)
    else:
        # No CORS if no origins configured (fail-safe)
        print("⚠️  WARNING: No ALLOWED_ORIGINS configured. CORS disabled for security.")
        CORS(app, origins=[], supports_credentials=False)

# Phase 2: Register Phase 2 API blueprint
try:
    from phase2.api import phase2_api
    from phase2.database import init_phase2_schema
    
    app.register_blueprint(phase2_api)
    
    # Initialize Phase 2 schema
    conn = get_connection()
    init_phase2_schema(conn)
    conn.close()
    
    PHASE2_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Phase 2 modules not available: {e}")
    PHASE2_AVAILABLE = False


# SECURITY: Limit concurrent SSE connections to prevent DoS
MAX_SSE_CONNECTIONS = 20
sse_semaphore = threading.Semaphore(MAX_SSE_CONNECTIONS)


def sse_stream_with_keepalive(event_generator):
    """
    Wrap an event generator with SSE keepalive comments.
    
    SECURITY: Limited to MAX_SSE_CONNECTIONS concurrent streams.
    
    Per spec:
    - Emit keepalive comments every 10 seconds
    - Close streams deterministically on completion or failure
    
    SSE Format:
    - Data events: "data: {...}\n\n"
    - Comments (keepalive): ": keepalive\n\n"
    """
    # SECURITY: Acquire semaphore or reject connection
    if not sse_semaphore.acquire(blocking=False):
        yield f"data: {json.dumps({'type': 'error', 'message': 'Too many active streams. Please try again later.'})}\n\n"
        return
    
    try:
        event_queue = Queue()
        is_complete = threading.Event()
        
        def producer():
            """Run the event generator in a background thread."""
            try:
                for event in event_generator:
                    event_queue.put(("data", event))
                    if event.get("type") == "complete":
                        break
            except Exception as e:
                event_queue.put(("error", str(e)))
            finally:
                is_complete.set()
                event_queue.put(("done", None))
        
        # Start producer thread
        producer_thread = threading.Thread(target=producer, daemon=True)
        producer_thread.start()
        
        last_event_time = time.time()
        
        while True:
            try:
                # Wait for events with timeout for keepalive
                event_type, event_data = event_queue.get(timeout=SSE_KEEPALIVE_INTERVAL)
                
                if event_type == "done":
                    break
                elif event_type == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': event_data})}\n\n"
                    break
                elif event_type == "data":
                    yield f"data: {json.dumps(event_data)}\n\n"
                    last_event_time = time.time()
                    
            except Empty:
                # No event received within timeout, send keepalive
                if is_complete.is_set():
                    break
                # SSE comment (keepalive) - per spec
                yield f": keepalive {datetime.utcnow().isoformat()}\n\n"
                last_event_time = time.time()
    finally:
        # SECURITY: Always release semaphore
        sse_semaphore.release()


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Railway."""
    return jsonify({
        "status": "healthy",
        "service": "model-scout-orchestrator",
        "version": "1.0.0-phase1",
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route("/api/sources", methods=["GET"])
def get_sources():
    """
    Return available benchmark sources.
    Phase 1 includes only 6 sources.
    """
    sources = []
    for key, config in BENCHMARK_SOURCES.items():
        sources.append({
            "key": key,
            "name": config["name"],
            "url": config["url"],
            "category": config["category"],
            "metrics": config["metrics"]
        })
    return jsonify({
        "sources": sources,
        "count": len(sources),
        "phase": "1"
    })


@app.route("/api/search", methods=["POST"])
def search_model():
    """
    Search for a model across all benchmark sources.
    Streams SSE events as Mino agents complete their tasks.
    
    Request body:
    {
        "model_name": "GPT-4o",
        "sources": ["huggingface", "lmsys_arena", ...]  // optional
    }
    
    SSE Event Shape (per spec):
    {
        "status": "running" | "completed" | "failed",
        "benchmark": "string",
        "message": "string"
    }
    """
    from validation import validate_model_name, validate_source_key, ValidationError
    
    data = request.json or {}
    model_name = data.get("model_name")
    sources = data.get("sources", list(BENCHMARK_SOURCES.keys()))
    
    # Validate model name
    if not model_name:
        return jsonify({"error": "model_name is required"}), 400
    
    try:
        model_name = validate_model_name(model_name)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    
    # Validate sources
    try:
        valid_sources = []
        for source in sources:
            validated = validate_source_key(source, list(BENCHMARK_SOURCES.keys()))
            valid_sources.append(validated)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    
    if not valid_sources:
        return jsonify({"error": "No valid sources specified"}), 400
    
    def generate():
        for event in parallel_snipe(model_name, valid_sources):
            yield event
    
    return Response(
        stream_with_context(sse_stream_with_keepalive(generate())),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )


@app.route("/api/compare", methods=["POST"])
def compare_models():
    """
    Compare two models across all benchmark sources.
    Streams SSE events with model identifiers.
    
    Request body:
    {
        "model_a": "GPT-4o",
        "model_b": "Claude 3.5 Sonnet",
        "sources": ["huggingface", "lmsys_arena", ...]  // optional
    }
    """
    data = request.json or {}
    model_a = data.get("model_a")
    model_b = data.get("model_b")
    sources = data.get("sources", list(BENCHMARK_SOURCES.keys()))
    
    if not model_a or not model_b:
        return jsonify({"error": "Both model_a and model_b are required"}), 400
    
    # Validate sources are in Phase 1 scope
    valid_sources = [s for s in sources if s in BENCHMARK_SOURCES]
    if not valid_sources:
        return jsonify({"error": "No valid sources specified"}), 400
    
    def generate():
        # Emit initial event
        init_event = {
            'type': 'init',
            'status': 'running',
            'model_a': model_a,
            'model_b': model_b,
            'sources': valid_sources,
            'timestamp': datetime.utcnow().isoformat()
        }
        yield init_event
        
        # Stream comparison events
        for event in parallel_compare(model_a, model_b, valid_sources):
            yield event
    
    return Response(
        stream_with_context(sse_stream_with_keepalive(generate())),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )


@app.route("/api/history/<model_name>", methods=["GET"])
def model_history(model_name: str):
    """Get historical benchmark data for a model."""
    limit = request.args.get("limit", 30, type=int)
    history = get_model_history(model_name, limit)
    return jsonify({"model": model_name, "history": history})


@app.route("/api/cached/<model_name>", methods=["GET"])
def get_cached(model_name: str):
    """Get cached results for a model if available."""
    source = request.args.get("source")
    max_age = request.args.get("max_age", 24, type=int)
    
    if source:
        result = get_cached_result(model_name, source, max_age)
        return jsonify({"model": model_name, "source": source, "result": result})
    
    # Get from all sources
    results = {}
    for source_key in BENCHMARK_SOURCES.keys():
        cached = get_cached_result(model_name, source_key, max_age)
        if cached:
            results[source_key] = cached
    
    return jsonify({"model": model_name, "results": results})


@app.route("/api/leaderboard", methods=["GET"])
def get_leaderboard():
    """
    Get the latest leaderboard data from the database (Phase 1 & 2 integration).
    Aggregates results from multiple benchmarks into a unified view.
    """
    try:
        from database import get_all_latest_benchmarks
        db_results = get_all_latest_benchmarks()
    except ImportError:
        return jsonify({"error": "Database utility not available"}), 500

    leaderboard = []
    
    for model_id, sources in db_results.items():
        # Basic model info
        parts = model_id.split('/')
        provider = parts[0].capitalize() if len(parts) > 1 else "Unknown"
        
        # Extract specific metrics
        mmlu = 0.0
        arena_elo = 0
        humaneval = 0.0
        context = 0
        safety = 0.0
        
        # Fill from sources (Source keys: huggingface, lmsys_arena, livecodebench, vellum, mask, vectara)
        if "huggingface" in sources:
            mmlu = sources["huggingface"].get("mmlu", sources["huggingface"].get("average_score", 0))
        
        if "lmsys_arena" in sources:
            arena_elo = sources["lmsys_arena"].get("arena_elo", sources["lmsys_arena"].get("average_score", 0))
            
        if "livecodebench" in sources:
            humaneval = sources["livecodebench"].get("humaneval", sources["livecodebench"].get("average_score", 0))
            
        if "vellum" in sources:
            metrics = sources["vellum"].get("metrics", sources["vellum"])
            context = metrics.get("context_window", 0)
            
        if "mask" in sources:
            safety = sources["mask"].get("average_score", 0)
        elif "vectara" in sources:
            safety = sources["vectara"].get("average_score", 0)
            
        # Calculate composite average
        scores_to_avg = []
        if mmlu > 0: scores_to_avg.append(float(mmlu))
        if arena_elo > 0: 
            # Normalize ELO: (elo - 1000) / 4 -> roughly maps 1000-1400 to 0-100
            scores_to_avg.append(max(0, min(100, (float(arena_elo) - 1000) / 4))) 
        if humaneval > 0: scores_to_avg.append(float(humaneval))
        if safety > 0: scores_to_avg.append(float(safety))
        
        average = sum(scores_to_avg) / len(scores_to_avg) if scores_to_avg else 0
        
        leaderboard.append({
            "model": model_id,
            "provider": provider,
            "mmlu": round(float(mmlu), 1),
            "arena_elo": int(arena_elo),
            "humaneval": round(float(humaneval), 1),
            "context": int(context),
            "safety": round(float(safety), 1),
            "average": round(float(average), 1),
            "rank": 0
        })
    
    # Sort by average score descending
    leaderboard = sorted(leaderboard, key=lambda x: x["average"], reverse=True)
    
    # Assign ranks
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1
        
    return jsonify({
        "status": "success",
        "updated_at": datetime.utcnow().isoformat(),
        "leaderboard": leaderboard
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    
    # SECURITY: Never enable debug mode in production
    # Debug mode can expose sensitive information and allow code execution
    flask_env = os.environ.get("FLASK_ENV", "production")
    debug = False
    
    if flask_env == "development":
        # Only allow debug in explicit development mode
        debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
        if debug:
            print("⚠️  WARNING: Debug mode is enabled. Do not use in production!")
    else:
        print("ℹ️  Running in production mode (debug disabled)")
    
    print(f"[*] Model Scout Orchestrator starting on port {port}")
    print(f"[*] Phase 1 - Vertical Slice")
    print(f"    Available sources: {list(BENCHMARK_SOURCES.keys())}")
    print(f"[*] Phase 1 endpoints:")
    print(f"    GET  /health")
    print(f"    GET  /api/sources")
    print(f"    POST /api/search")
    print(f"    POST /api/compare")
    print(f"    GET  /api/history/<model>")
    print(f"    GET  /api/cached/<model>")
    print(f"    GET  /api/leaderboard")
    
    if PHASE2_AVAILABLE:
        print(f"[*] Phase 2 endpoints (ACTIVE):")
        print(f"    GET  /api/v2/prs/<model_id>")
        print(f"    GET  /api/v2/snapshots")
        print(f"    GET  /api/v2/snapshots/<id>/verify")
        print(f"    GET  /api/v2/snapshots/diff")
        print(f"    POST /api/v2/regressions/detect/<model_id>")
        print(f"    GET  /api/v2/regressions/history")
        print(f"    GET  /api/v2/frontier")
        print(f"    GET  /api/v2/docs/prs")
        
        # Check if analyst module is available
        try:
            from phase2.api import ANALYST_AVAILABLE
            if ANALYST_AVAILABLE:
                print(f"[INFO] Phase 2 AI Analyst endpoints (ACTIVE):")
                print(f"    POST /api/v2/analyst/recommend")
                print(f"    POST /api/v2/analyst/recommend/ai  [Gemini AI]")
                print(f"    POST /api/v2/analyst/disqualify/<model_id>")
                print(f"    POST /api/v2/analyst/compare")
                print(f"    GET  /api/v2/analyst/cost/<model_id>")
                print(f"    GET  /api/v2/analyst/data-status")
                print(f"    GET  /api/v2/analyst/models")
                print(f"    GET  /api/v2/docs/analyst")
            else:
                print(f"[!] Phase 2 AI Analyst module NOT loaded")
        except:
            pass
    else:
        print(f"[!] Phase 2 endpoints NOT available")
    
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)


