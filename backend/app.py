"""
Model Scout - Flask API Server (Phase 1)
Main orchestration layer connecting frontend to Mino agents

PHASE 1 REQUIREMENTS:
- SSE (text/event-stream) live logs
- Keepalive comments every 10 seconds
- Close streams deterministically on completion or failure
"""
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
CORS(app, origins=["http://localhost:8080", "http://localhost:3000", "*"])

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


def sse_stream_with_keepalive(event_generator):
    """
    Wrap an event generator with SSE keepalive comments.
    
    Per spec:
    - Emit keepalive comments every 10 seconds
    - Close streams deterministically on completion or failure
    
    SSE Format:
    - Data events: "data: {...}\n\n"
    - Comments (keepalive): ": keepalive\n\n"
    """
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
    data = request.json or {}
    model_name = data.get("model_name")
    sources = data.get("sources", list(BENCHMARK_SOURCES.keys()))
    
    if not model_name:
        return jsonify({"error": "model_name is required"}), 400
    
    # Validate sources are in Phase 1 scope
    valid_sources = [s for s in sources if s in BENCHMARK_SOURCES]
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
    Get aggregated leaderboard data.
    Returns sample data for demonstration; production would query database.
    
    Note: This is mock data for Phase 1 demonstration purposes.
    In production, this would aggregate data from the SQLite database.
    """
    leaderboard = [
        {
            "rank": 1,
            "model": "GPT-4o",
            "model_id": "openai/gpt-4o",
            "provider": "OpenAI",
            "mmlu": 88.7,
            "arena_elo": 1287,
            "humaneval": 90.2,
            "hallucination_rate": 3.2,  # Lower is better
            "average": 89.0
        },
        {
            "rank": 2,
            "model": "Claude 3.5 Sonnet",
            "model_id": "anthropic/claude-3.5-sonnet",
            "provider": "Anthropic",
            "mmlu": 88.3,
            "arena_elo": 1272,
            "humaneval": 92.0,
            "hallucination_rate": 2.8,
            "average": 88.5
        },
        {
            "rank": 3,
            "model": "Gemini 1.5 Pro",
            "model_id": "google/gemini-1.5-pro",
            "provider": "Google",
            "mmlu": 85.9,
            "arena_elo": 1260,
            "humaneval": 84.1,
            "hallucination_rate": 4.1,
            "average": 85.2
        },
        {
            "rank": 4,
            "model": "Llama-3-70B-Instruct",
            "model_id": "meta/llama-3-70b-instruct",
            "provider": "Meta",
            "mmlu": 82.0,
            "arena_elo": 1207,
            "humaneval": 81.7,
            "hallucination_rate": 5.3,
            "average": 81.5
        },
        {
            "rank": 5,
            "model": "DeepSeek-V2-Chat",
            "model_id": "deepseek/deepseek-v2-chat",
            "provider": "DeepSeek",
            "mmlu": 84.2,
            "arena_elo": 1189,
            "humaneval": 84.3,
            "hallucination_rate": 4.7,
            "average": 82.8
        },
        {
            "rank": 6,
            "model": "Qwen2-72B-Instruct",
            "model_id": "alibaba/qwen2-72b-instruct",
            "provider": "Alibaba",
            "mmlu": 84.2,
            "arena_elo": 1187,
            "humaneval": 86.0,
            "hallucination_rate": 4.9,
            "average": 84.5
        },
        {
            "rank": 7,
            "model": "Mistral-Large-2",
            "model_id": "mistral/mistral-large-2",
            "provider": "Mistral",
            "mmlu": 84.0,
            "arena_elo": 1158,
            "humaneval": 89.0,
            "hallucination_rate": 5.1,
            "average": 85.0
        },
        {
            "rank": 8,
            "model": "Command R+",
            "model_id": "cohere/command-r-plus",
            "provider": "Cohere",
            "mmlu": 75.7,
            "arena_elo": 1147,
            "humaneval": 75.0,
            "hallucination_rate": 6.2,
            "average": 75.3
        }
    ]
    
    return jsonify({
        "leaderboard": leaderboard,
        "updated_at": datetime.utcnow().isoformat(),
        "phase": "1",
        "note": "Sample data for Phase 1 demonstration"
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    
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
    else:
        print(f"[!] Phase 2 endpoints NOT available")
    
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)


