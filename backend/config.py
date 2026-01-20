"""
Model Scout - Configuration (Phase 1)
Environment variables and benchmark source configurations

PHASE 1 SCOPE (STRICT — ENFORCED):
Only the following benchmarks are included:
- General: HuggingFace Open LLM Leaderboard, LMSYS Chatbot Arena
- Economics: Vellum.ai (cost, speed, context window)
- Coding: LiveCodeBench
- Safety: MASK (Scale.com), Vectara Hallucination Leaderboard

Do NOT add additional benchmarks without explicit approval.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# MINO API CONFIGURATION
# =============================================================================

MINO_API_URL = "https://mino.ai/v1/automation/run-sse"
MINO_API_KEY = os.environ.get("MINO_API_KEY", "")

# =============================================================================
# THREADPOOLEXECUTOR SETTINGS (MANDATORY)
# max_workers=5 as per spec
# =============================================================================

MAX_WORKERS = 5
REQUEST_TIMEOUT = 180  # seconds

# =============================================================================
# SSE KEEPALIVE INTERVAL
# Emit keepalive comments every 10 seconds as per spec
# =============================================================================

SSE_KEEPALIVE_INTERVAL = 10  # seconds

# =============================================================================
# MINO EXTRACTION PROMPT (EXACT — DO NOT DEVIATE)
# This is the verbatim instruction sent to Mino for all benchmark extractions
# =============================================================================

MINO_EXTRACTION_PROMPT = """You are an autonomous benchmark extraction agent.

TASK:
Extract model performance data from the provided URL.

RULES:
- Extract ONLY what is explicitly present.
- Do NOT infer missing values.
- Do NOT normalize.
- Preserve metric names and units exactly.
- If a value is unavailable, return null.
- If extraction fails, return error_code.

OUTPUT:
Strict JSON following the provided schema."""

# =============================================================================
# BENCHMARK SOURCE CONFIGURATIONS — PHASE 1 ONLY (6 SOURCES)
# =============================================================================

BENCHMARK_SOURCES = {
    # =========================================================================
    # GENERAL INTELLIGENCE
    # =========================================================================
    
    "huggingface": {
        "name": "HuggingFace Open LLM Leaderboard",
        "url": "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard",
        "category": "general",
        "metrics": ["mmlu", "arc_challenge", "hellaswag", "truthfulqa", "winogrande", "gsm8k"],
        "goal_template": """Search for the model "{model_name}" in the leaderboard. Extract its rank, average score, and individual benchmark scores (MMLU, ARC, HellaSwag, TruthfulQA, WinoGrande, GSM8K). Return as JSON with keys: model, rank, average_score, benchmark_metrics (object with each score)."""
    },
    
    "lmsys_arena": {
        "name": "LMSYS Chatbot Arena",
        "url": "https://lmarena.ai/leaderboard",
        "category": "general",
        "metrics": ["arena_elo", "votes_count", "win_rate"],
        "goal_template": """Find the model "{model_name}" in the Arena leaderboard. Extract its Arena ELO rating, rank position, and vote statistics if visible. Return as JSON with keys: model, rank, arena_elo, average_score (use ELO as the score)."""
    },
    
    # =========================================================================
    # ECONOMICS
    # =========================================================================
    
    "vellum": {
        "name": "Vellum LLM Leaderboard",
        "url": "https://vellum.ai/llm-leaderboard",
        "category": "economics",
        "metrics": ["input_price", "output_price", "speed", "latency", "context_window"],
        "goal_template": """Find "{model_name}" in the LLM comparison table. Extract: input price per 1M tokens, output price per 1M tokens, speed (tokens/sec), latency, and context window size. Return as JSON with keys: model, input_price, output_price, speed_tps, latency_ms, context_window."""
    },
    
    # =========================================================================
    # CODING
    # =========================================================================
    
    "livecodebench": {
        "name": "LiveCodeBench",
        "url": "https://livecodebench.github.io/leaderboard.html",
        "category": "coding",
        "metrics": ["pass_at_1", "humaneval", "mbpp"],
        "goal_template": """Search for "{model_name}" on the LiveCodeBench leaderboard. Extract pass@1 rate, HumanEval score, and MBPP score. Return as JSON with keys: model, rank, pass_at_1, humaneval, mbpp."""
    },
    
    # =========================================================================
    # SAFETY
    # =========================================================================
    
    "mask": {
        "name": "MASK Deception Benchmark",
        "url": "https://scale.com/leaderboard/mask",
        "category": "safety",
        "metrics": ["lying_rate", "manipulation_score", "deception_score"],
        # NOTE: Lower is better for safety metrics
        "invert_score": True,
        "goal_template": """Find "{model_name}" on the MASK leaderboard. Extract lying rate, manipulation score, and deception metrics. Lower is better. Return as JSON with keys: model, rank, lying_rate, manipulation_score."""
    },
    
    "vectara": {
        "name": "Vectara Hallucination Leaderboard",
        "url": "https://github.com/vectara/hallucination-leaderboard",
        "category": "safety",
        "metrics": ["hallucination_rate", "factual_accuracy"],
        # NOTE: Lower hallucination_rate is better
        "invert_score": True,
        "goal_template": """Search for "{model_name}" in the Vectara hallucination leaderboard README or table. Extract hallucination rate percentage. Lower is better. Return as JSON with keys: model, rank, hallucination_rate."""
    },
}

# =============================================================================
# SOURCE CATEGORIES FOR UI GROUPING
# =============================================================================

SOURCE_CATEGORIES = {
    "general": {
        "name": "General Intelligence",
        "description": "Broad capability benchmarks",
        "sources": ["huggingface", "lmsys_arena"]
    },
    "economics": {
        "name": "Product Economics",
        "description": "Cost, speed, and efficiency metrics",
        "sources": ["vellum"]
    },
    "coding": {
        "name": "Coding & Development",
        "description": "Programming and code generation",
        "sources": ["livecodebench"]
    },
    "safety": {
        "name": "Safety & Alignment",
        "description": "Hallucination, deception, robustness",
        "sources": ["mask", "vectara"]
    }
}

# =============================================================================
# RADAR CHART CATEGORIES (For Capability Fingerprint)
# 5 axes: Logic, Coding, Math, Safety, General
# =============================================================================

RADAR_CATEGORIES = {
    "logic": {
        "name": "Logic",
        "sources": ["huggingface", "lmsys_arena"],
        "weight": 1.0
    },
    "coding": {
        "name": "Coding",
        "sources": ["livecodebench"],
        "weight": 1.0
    },
    "economics": {
        "name": "Economics",
        "sources": ["vellum"],
        "weight": 1.0
    },
    "safety": {
        "name": "Safety",
        "sources": ["mask", "vectara"],
        "weight": 1.0
    }
}

# =============================================================================
# MODEL IDENTIFIER MAPPING
# Maps raw model names from benchmarks to canonical internal model_id
# This is a simple explicit mapping as required by spec
# =============================================================================

MODEL_ID_MAPPING = {
    # OpenAI Models
    "gpt-4o": "openai/gpt-4o",
    "gpt-4o": "openai/gpt-4o",
    "gpt-4o-2024-08": "openai/gpt-4o",
    "gpt-4o-2024-05-13": "openai/gpt-4o",
    "gpt-4-turbo": "openai/gpt-4-turbo",
    "gpt-4": "openai/gpt-4",
    "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
    
    # Anthropic Models
    "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
    "claude-3-5-sonnet-20240620": "anthropic/claude-3.5-sonnet",
    "claude-3-opus": "anthropic/claude-3-opus",
    "claude-3-sonnet": "anthropic/claude-3-sonnet",
    "claude-3-haiku": "anthropic/claude-3-haiku",
    
    # Google Models
    "gemini-1.5-pro": "google/gemini-1.5-pro",
    "gemini-1.5-flash": "google/gemini-1.5-flash",
    "gemini-pro": "google/gemini-pro",
    
    # Meta Models
    "llama-3-70b-instruct": "meta/llama-3-70b-instruct",
    "llama-3-8b-instruct": "meta/llama-3-8b-instruct",
    "llama-3.1-405b-instruct": "meta/llama-3.1-405b-instruct",
    "llama-3.1-70b-instruct": "meta/llama-3.1-70b-instruct",
    "llama-3.1-8b-instruct": "meta/llama-3.1-8b-instruct",
    
    # Mistral Models
    "mistral-large": "mistral/mistral-large",
    "mistral-large-2": "mistral/mistral-large-2",
    "mistral-medium": "mistral/mistral-medium",
    "mistral-small": "mistral/mistral-small",
    "mixtral-8x7b": "mistral/mixtral-8x7b",
    
    # DeepSeek Models
    "deepseek-v2-chat": "deepseek/deepseek-v2-chat",
    "deepseek-coder": "deepseek/deepseek-coder",
    
    # Alibaba Models
    "qwen2-72b-instruct": "alibaba/qwen2-72b-instruct",
    "qwen2-7b-instruct": "alibaba/qwen2-7b-instruct",
    
    # Cohere Models
    "command-r-plus": "cohere/command-r-plus",
    "command-r": "cohere/command-r",
}


def get_canonical_model_id(raw_model_name: str) -> str:
    """
    Resolve a raw model name to a canonical internal model_id.
    
    Logic:
    1. Normalize the raw name (lowercase, strip whitespace)
    2. Check if it's in the explicit mapping
    3. If not, return the normalized name as-is
    
    This ensures all models have a consistent identifier across sources.
    """
    normalized = raw_model_name.lower().strip()
    
    # Remove common prefixes/suffixes
    normalized = normalized.replace("meta-llama/", "")
    normalized = normalized.replace("openai/", "")
    normalized = normalized.replace("anthropic/", "")
    
    # Check mapping
    if normalized in MODEL_ID_MAPPING:
        return MODEL_ID_MAPPING[normalized]
    
    # Return as-is if not in mapping, preserving original format
    return raw_model_name


# =============================================================================
# NORMALIZATION RULES (PHASE 1 — SIMPLE)
# Document logic inline as per spec
# =============================================================================

def normalize_score(raw_score: float, metric_name: str, source_key: str) -> float:
    """
    Normalize a raw benchmark score to 0-100 scale.
    
    NORMALIZATION RULES (from spec):
    1. Normalize numeric scores to 0-100
    2. Higher is always better (after normalization)
    3. Missing benchmarks do NOT penalize
    4. If a metric is lower-is-better, invert before normalization
    5. No weighting
    6. No ML
    
    Args:
        raw_score: The raw score value from the benchmark
        metric_name: Name of the metric (e.g., 'mmlu', 'hallucination_rate')
        source_key: Key of the source (e.g., 'huggingface', 'mask')
        
    Returns:
        Normalized score in 0-100 range where higher is better
    """
    if raw_score is None:
        return None
    
    # Check if this is a lower-is-better metric that needs inversion
    # Safety metrics: lower lying_rate, hallucination_rate = better
    invert_metrics = {
        'lying_rate',
        'manipulation_score', 
        'deception_score',
        'hallucination_rate',
    }
    
    should_invert = (
        metric_name.lower() in invert_metrics or
        BENCHMARK_SOURCES.get(source_key, {}).get('invert_score', False)
    )
    
    # Handle ELO scores (typically 1000-1500 range)
    if metric_name.lower() in ['arena_elo', 'elo']:
        # Normalize ELO to 0-100 assuming 1000-1500 range
        # 1000 = 0, 1500 = 100
        normalized = ((raw_score - 1000) / 500) * 100
        return max(0, min(100, normalized))
    
    # Handle percentage scores (already 0-100)
    if raw_score <= 100:
        if should_invert:
            # Invert: 0% rate = 100 score, 100% rate = 0 score
            return 100 - raw_score
        return max(0, min(100, raw_score))
    
    # Handle other large scores (normalize assuming max is the current value)
    # This is a fallback for unknown score ranges
    return max(0, min(100, raw_score))


# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

DATABASE_PATH = os.environ.get("DATABASE_PATH", "./modelscout.db")
