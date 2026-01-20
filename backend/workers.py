"""
Model Scout - Mino Worker Module (Phase 1)
Handles parallel execution of Mino agents using ThreadPoolExecutor

PHASE 1 REQUIREMENTS:
- ThreadPoolExecutor(max_workers=5) for parallel extraction
- Each benchmark runs independently
- Failures must not block other benchmarks
- SSE events with status: running | completed | failed
"""
import json
import re
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Generator, List, Tuple, Dict, Any, Optional

from config import (
    MINO_API_URL,
    MINO_API_KEY,
    BENCHMARK_SOURCES,
    MAX_WORKERS,
    REQUEST_TIMEOUT,
    MINO_EXTRACTION_PROMPT,
    get_canonical_model_id,
    normalize_score,
)
from database import save_benchmark_result, get_cached_result


def extract_numeric(value: Any) -> Optional[float]:
    """
    Extract a numeric value from various formats.
    
    Handles:
    - Direct numbers (int, float)
    - N/A values → None
    - Strings like "89.1% (Pass@1)" → 89.1
    - Strings like "1287" → 1287.0
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Skip N/A values
        if value.lower() in ['n/a', 'na', 'null', 'none', '-', '']:
            return None
        # Extract number from strings like "89.1% (Pass@1)" or "1287"
        match = re.search(r'(\d+\.?\d*)', value)
        if match:
            return float(match.group(1))
    return None


class MinoWorker:
    """
    Worker class for executing Mino automation agents.
    Handles SSE streaming and result parsing.
    
    Mino Contract (from spec):
    - Mino accepts (URL + extraction instruction)
    - Returns structured JSON or explicit failure
    - Never stores state
    - Never ranks or normalizes
    """
    
    def __init__(self, use_cache: bool = True, cache_max_age_hours: int = 24):
        self.use_cache = use_cache
        self.cache_max_age_hours = cache_max_age_hours
        self.headers = {
            "X-API-Key": MINO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
    
    def _create_goal(self, source_key: str, model_name: str) -> str:
        """
        Generate the goal prompt for a specific benchmark source.
        Uses the goal_template from config for source-specific instructions.
        """
        source = BENCHMARK_SOURCES.get(source_key)
        if not source:
            raise ValueError(f"Unknown source: {source_key}")
        
        return source["goal_template"].format(model_name=model_name)
    
    def _parse_sse_event(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse an SSE data payload into a structured event."""
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {"type": "log", "message": data}
    
    def _normalize_mino_response(
        self, 
        raw_data: Dict[str, Any], 
        source_key: str, 
        model_name: str
    ) -> Dict[str, Any]:
        """
        Normalize Mino API response to our standard format.
        
        Mino Output Contract (STRICT from spec):
        {
          "status": "success" | "failure",
          "payload": {
            "benchmark": "string",
            "model": "string",
            "metrics": { "<metric_name>": "number | string | null" },
            "rank": "number | null",
            "source_url": "string",
            "timestamp_utc": "string"
          },
          "error_code": null | "UNREADABLE_FORMAT" | "SITE_BLOCKED" | "LAYOUT_CHANGED"
        }
        """
        # Check for not_found status
        status = raw_data.get('Status', raw_data.get('status', ''))
        if isinstance(status, str) and 'not_found' in status.lower():
            return {
                "model": get_canonical_model_id(model_name),
                "error": "MODEL_NOT_FOUND",
                "message": f"{model_name} not found on {source_key}",
                "source": source_key
            }
        
        # Normalize field names (handle both camelCase and snake_case)
        normalized = {
            "model": get_canonical_model_id(
                raw_data.get('Model') or raw_data.get('model') or model_name
            ),
            "source": source_key,
        }
        
        # Extract rank
        rank_value = raw_data.get('Rank') or raw_data.get('rank')
        if rank_value:
            if isinstance(rank_value, int):
                normalized["rank"] = rank_value
            elif isinstance(rank_value, str):
                match = re.search(r'(\d+)', rank_value)
                if match:
                    normalized["rank"] = int(match.group(1))
        else:
            normalized["rank"] = None
        
        # Extract main score
        score_value = (
            raw_data.get('Score') or 
            raw_data.get('score') or 
            raw_data.get('Average Score') or 
            raw_data.get('average_score') or
            raw_data.get('arena_elo') or
            raw_data.get('Arena ELO')
        )
        normalized["average_score"] = extract_numeric(score_value)
        
        # Build benchmark_metrics from available data
        # NORMALIZATION RULES (from spec):
        # 1. Normalize to 0-100
        # 2. Higher is always better
        # 3. Invert lower-is-better metrics
        metrics = {}
        
        # Look for specific benchmark fields
        metric_keys = {
            'mmlu': ['MMLU', 'mmlu'],
            'arc_challenge': ['ARC', 'arc', 'arc_challenge'],
            'hellaswag': ['HellaSwag', 'hellaswag'],
            'truthfulqa': ['TruthfulQA', 'truthfulqa'],
            'winogrande': ['WinoGrande', 'winogrande'],
            'gsm8k': ['GSM8K', 'gsm8k'],
            'humaneval': ['HumanEval', 'humaneval', 'pass@1', 'Pass@1'],
            'arena_elo': ['Arena ELO', 'arena_elo', 'ELO', 'elo'],
            'mbpp': ['MBPP', 'mbpp'],
            'pass_at_1': ['pass_at_1', 'Pass@1', 'pass@1'],
            # Safety metrics (lower is better - will be inverted)
            'hallucination_rate': ['hallucination_rate', 'Hallucination Rate'],
            'lying_rate': ['lying_rate', 'Lying Rate'],
            'manipulation_score': ['manipulation_score', 'Manipulation Score'],
            # Economics metrics
            'input_price': ['input_price', 'Input Price'],
            'output_price': ['output_price', 'Output Price'],
            'speed_tps': ['speed_tps', 'speed', 'Speed'],
            'latency_ms': ['latency_ms', 'latency', 'Latency'],
            'context_window': ['context_window', 'Context Window'],
        }
        
        for metric_name, possible_keys in metric_keys.items():
            for key in possible_keys:
                if key in raw_data:
                    raw_value = extract_numeric(raw_data[key])
                    if raw_value is not None:
                        # Apply normalization per spec rules
                        metrics[metric_name] = normalize_score(
                            raw_value, metric_name, source_key
                        )
                        break
        
        # If we have a main score but no metrics, use the score as the primary metric
        if not metrics and normalized["average_score"]:
            if source_key == "lmsys_arena":
                metrics["arena_elo"] = normalized["average_score"]
            elif source_key == "livecodebench":
                metrics["pass_at_1"] = normalized["average_score"]
            else:
                metrics["score"] = normalized["average_score"]
        
        normalized["benchmark_metrics"] = metrics
        
        return normalized
    
    def snipe_benchmark(
        self, 
        source_key: str, 
        model_name: str
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Execute a single Mino agent to extract benchmark data.
        Streams SSE responses and yields parsed chunks.
        
        SSE Event Shape (from spec):
        {
          "status": "running" | "completed" | "failed",
          "benchmark": "string",
          "message": "string"
        }
        
        Args:
            source_key: Key identifying the benchmark source (e.g., 'huggingface')
            model_name: Name of the model to search for
            
        Yields:
            Dict containing event data with keys: source, type, data, timestamp
        """
        # Yield initial running status
        yield {
            "source": source_key,
            "type": "status",
            "status": "running",
            "benchmark": BENCHMARK_SOURCES[source_key]["name"],
            "message": f"Starting extraction from {BENCHMARK_SOURCES[source_key]['name']}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check cache first
        if self.use_cache:
            cached = get_cached_result(model_name, source_key, self.cache_max_age_hours)
            if cached:
                yield {
                    "source": source_key,
                    "type": "cache_hit",
                    "status": "completed",
                    "benchmark": BENCHMARK_SOURCES[source_key]["name"],
                    "data": cached,
                    "message": f"Cache hit for {model_name} on {source_key}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield {
                    "source": source_key,
                    "type": "result",
                    "status": "completed",
                    "data": cached,
                    "timestamp": datetime.utcnow().isoformat()
                }
                return
        
        goal = self._create_goal(source_key, model_name)
        source_url = BENCHMARK_SOURCES[source_key]['url']
        
        payload = {
            "url": source_url,
            "goal": goal,
            "systemPrompt": MINO_EXTRACTION_PROMPT,
            "browserProfile": "stealth"
        }
        
        yield {
            "source": source_key,
            "type": "log",
            "status": "running",
            "benchmark": BENCHMARK_SOURCES[source_key]["name"],
            "message": f"Connecting to {BENCHMARK_SOURCES[source_key]['name']}...",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            with requests.post(
                MINO_API_URL,
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=REQUEST_TIMEOUT
            ) as response:
                response.raise_for_status()
                
                yield {
                    "source": source_key,
                    "type": "log",
                    "status": "running",
                    "benchmark": BENCHMARK_SOURCES[source_key]["name"],
                    "message": f"Connected. Fetching data from {BENCHMARK_SOURCES[source_key]['url']}...",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                buffer = ""
                final_result = None
                
                for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        buffer += chunk
                        
                        # Parse SSE format: "data: {...}\n\n"
                        while "\n\n" in buffer:
                            event_str, buffer = buffer.split("\n\n", 1)
                            
                            if event_str.startswith("data: "):
                                data = event_str[6:]  # Strip "data: " prefix
                                parsed = self._parse_sse_event(data)
                                
                                if parsed:
                                    event_type = parsed.get("type", "log")
                                    
                                    # Handle Mino's COMPLETE event type
                                    if event_type == "COMPLETE" or parsed.get("status") == "COMPLETED":
                                        # Extract resultJson from Mino response
                                        result_data = parsed.get("resultJson") or parsed.get("result") or parsed.get("data")
                                        if result_data and isinstance(result_data, dict):
                                            # Normalize the result data
                                            normalized = self._normalize_mino_response(result_data, source_key, model_name)
                                            if normalized and normalized.get("average_score") is not None:
                                                final_result = normalized
                                                yield {
                                                    "source": source_key,
                                                    "type": "result",
                                                    "status": "completed",
                                                    "benchmark": BENCHMARK_SOURCES[source_key]["name"],
                                                    "data": normalized,
                                                    "timestamp": datetime.utcnow().isoformat()
                                                }
                                            else:
                                                # Result was N/A or not found
                                                yield {
                                                    "source": source_key,
                                                    "type": "warning",
                                                    "status": "completed",
                                                    "benchmark": BENCHMARK_SOURCES[source_key]["name"],
                                                    "message": f"Model not found or no data available on {BENCHMARK_SOURCES[source_key]['name']}",
                                                    "timestamp": datetime.utcnow().isoformat()
                                                }
                                        continue
                                    
                                    # Handle regular log events
                                    event = {
                                        "source": source_key,
                                        "type": event_type.lower() if event_type else "log",
                                        "status": "running",
                                        "benchmark": BENCHMARK_SOURCES[source_key]["name"],
                                        "data": parsed.get("data") or parsed.get("message") or data,
                                        "timestamp": datetime.utcnow().isoformat()
                                    }
                                    
                                    # Check if this is a result event
                                    if event_type.lower() in ["result", "data"]:
                                        final_result = parsed.get("data", parsed)
                                    
                                    yield event
                
                # Process any remaining buffer
                if buffer.startswith("data: "):
                    data = buffer[6:]
                    parsed = self._parse_sse_event(data)
                    if parsed:
                        event_type = parsed.get("type", "")
                        if event_type == "COMPLETE" or parsed.get("status") == "COMPLETED":
                            result_data = parsed.get("resultJson") or parsed.get("result") or parsed.get("data")
                            if result_data and isinstance(result_data, dict):
                                normalized = self._normalize_mino_response(result_data, source_key, model_name)
                                if normalized and normalized.get("average_score") is not None:
                                    final_result = normalized
                                    yield {
                                        "source": source_key,
                                        "type": "result",
                                        "status": "completed",
                                        "benchmark": BENCHMARK_SOURCES[source_key]["name"],
                                        "data": normalized,
                                        "timestamp": datetime.utcnow().isoformat()
                                    }
                        elif event_type.lower() in ["result", "data"]:
                            result_data = parsed.get("data", parsed)
                            if isinstance(result_data, dict):
                                normalized = self._normalize_mino_response(result_data, source_key, model_name)
                                if normalized and normalized.get("average_score") is not None:
                                    final_result = normalized
                                    yield {
                                        "source": source_key,
                                        "type": "result",
                                        "status": "completed",
                                        "benchmark": BENCHMARK_SOURCES[source_key]["name"],
                                        "data": normalized,
                                        "timestamp": datetime.utcnow().isoformat()
                                    }
                
                # Save result to cache
                if final_result and not final_result.get("error"):
                    save_benchmark_result(model_name, source_key, final_result)
                    
                yield {
                    "source": source_key,
                    "type": "done",
                    "status": "completed",
                    "benchmark": BENCHMARK_SOURCES[source_key]["name"],
                    "message": f"Completed extraction from {BENCHMARK_SOURCES[source_key]['name']}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                    
        except requests.exceptions.Timeout:
            yield {
                "source": source_key,
                "type": "error",
                "status": "failed",
                "benchmark": BENCHMARK_SOURCES[source_key]["name"],
                "message": f"Timeout while fetching from {BENCHMARK_SOURCES[source_key]['name']}",
                "error_code": "TIMEOUT",
                "timestamp": datetime.utcnow().isoformat()
            }
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            yield {
                "source": source_key,
                "type": "error",
                "status": "failed",
                "benchmark": BENCHMARK_SOURCES[source_key]["name"],
                "message": f"Connection error: {error_msg[:100]}",
                "error_code": "CONNECTION_ERROR",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            yield {
                "source": source_key,
                "type": "error",
                "status": "failed",
                "benchmark": BENCHMARK_SOURCES[source_key]["name"],
                "message": f"Error: {str(e)[:100]}",
                "error_code": "UNKNOWN_ERROR",
                "timestamp": datetime.utcnow().isoformat()
            }


def parallel_snipe(
    model_name: str,
    sources: List[str] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Orchestrate parallel Mino agents across multiple benchmark sources.
    Uses ThreadPoolExecutor(max_workers=5) for concurrent execution.
    
    Per spec requirements:
    - Each benchmark runs independently
    - Failures must not block other benchmarks
    
    Args:
        model_name: Name of the model to search for
        sources: List of source keys to query (default: all Phase 1 sources)
        
    Yields:
        Dict containing event data from all workers
    """
    if sources is None:
        sources = list(BENCHMARK_SOURCES.keys())
    
    worker = MinoWorker()
    
    yield {
        "source": "orchestrator",
        "type": "system",
        "status": "running",
        "message": f"Starting parallel extraction for '{model_name}' across {len(sources)} sources",
        "sources": sources,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Collect all events from parallel workers
    # ThreadPoolExecutor(max_workers=5) as per spec
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_source = {
            executor.submit(lambda s: list(worker.snipe_benchmark(s, model_name)), source): source
            for source in sources
        }
        
        # Yield results as they complete
        # Failures in one benchmark do not block others
        for future in as_completed(future_to_source):
            source = future_to_source[future]
            try:
                events = future.result()
                for event in events:
                    yield event
            except Exception as e:
                # Failure in one source does not block others
                yield {
                    "source": source,
                    "type": "error",
                    "status": "failed",
                    "benchmark": BENCHMARK_SOURCES.get(source, {}).get("name", source),
                    "message": f"Worker failed: {str(e)}",
                    "error_code": "WORKER_FAILURE",
                    "timestamp": datetime.utcnow().isoformat()
                }
    
    yield {
        "source": "orchestrator",
        "type": "complete",
        "status": "completed",
        "message": "All sources processed",
        "timestamp": datetime.utcnow().isoformat()
    }


def parallel_compare(
    model_a: str,
    model_b: str,
    sources: List[str] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Execute parallel comparison of two models across benchmark sources.
    
    Args:
        model_a: First model name
        model_b: Second model name
        sources: List of source keys to query
        
    Yields:
        Dict containing event data with model identifier
    """
    if sources is None:
        sources = list(BENCHMARK_SOURCES.keys())
    
    worker = MinoWorker()
    tasks: List[Tuple[str, str]] = []
    
    for source in sources:
        tasks.append((source, model_a))
        tasks.append((source, model_b))
    
    yield {
        "source": "orchestrator",
        "type": "system",
        "status": "running",
        "message": f"Starting comparison: '{model_a}' vs '{model_b}' across {len(sources)} sources",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_task = {
            executor.submit(lambda t: list(worker.snipe_benchmark(t[0], t[1])), task): task
            for task in tasks
        }
        
        for future in as_completed(future_to_task):
            source, model = future_to_task[future]
            try:
                events = future.result()
                for event in events:
                    event["model"] = model
                    yield event
            except Exception as e:
                yield {
                    "source": source,
                    "model": model,
                    "type": "error",
                    "status": "failed",
                    "benchmark": BENCHMARK_SOURCES.get(source, {}).get("name", source),
                    "message": f"Worker failed: {str(e)}",
                    "error_code": "WORKER_FAILURE",
                    "timestamp": datetime.utcnow().isoformat()
                }
    
    yield {
        "source": "orchestrator",
        "type": "complete",
        "status": "completed",
        "message": "Comparison complete",
        "timestamp": datetime.utcnow().isoformat()
    }
