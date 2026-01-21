"""
ModelScout Phase 2 - AI Model Analyst Module

This module implements the Phase 2 system prompt specification:
- Model Recommendation Explanation
- "Why NOT This Model?" Disqualifier Mode
- Model Comparison Mode (Side-by-Side)
- Cost Transparency (Mandatory)
- Data Trust & Freshness

CORE PRINCIPLE: Help users make confident model decisions by understanding tradeoffs, not by chasing rankings.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import json

# Add import for database interaction
try:
    from ..database import get_all_latest_benchmarks
    DATABASE_AVAILABLE = True
except (ImportError, ValueError):
    # Fallback for direct execution or if structure differs
    try:
        from database import get_all_latest_benchmarks
        DATABASE_AVAILABLE = True
    except:
        DATABASE_AVAILABLE = False


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ContextLength(Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


# Model pricing data (from real-world sources)
# Updated: January 2026
MODEL_PRICING = {
    "gpt-4o": {"input": 5.00, "output": 15.00, "provider": "OpenAI"},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "provider": "OpenAI"},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00, "provider": "OpenAI"},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50, "provider": "OpenAI"},
    "claude-3.5-sonnet": {"input": 3.00, "output": 15.00, "provider": "Anthropic"},
    "claude-3-opus": {"input": 15.00, "output": 75.00, "provider": "Anthropic"},
    "claude-3-haiku": {"input": 0.25, "output": 1.25, "provider": "Anthropic"},
    "gemini-1.5-pro": {"input": 3.50, "output": 10.50, "provider": "Google"},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30, "provider": "Google"},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40, "provider": "Google"},
    "llama-3-70b-instruct": {"input": 0.90, "output": 0.90, "provider": "Meta"},
    "llama-3.1-405b": {"input": 3.00, "output": 3.00, "provider": "Meta"},
    "llama-3.1-70b": {"input": 0.90, "output": 0.90, "provider": "Meta"},
    "llama-3.1-8b": {"input": 0.18, "output": 0.18, "provider": "Meta"},
    "mistral-large-2": {"input": 2.00, "output": 6.00, "provider": "Mistral"},
    "mistral-small": {"input": 0.20, "output": 0.60, "provider": "Mistral"},
    "deepseek-v3": {"input": 0.27, "output": 1.10, "provider": "DeepSeek"},
    "deepseek-v2": {"input": 0.14, "output": 0.28, "provider": "DeepSeek"},
    "qwen2.5-72b": {"input": 0.90, "output": 0.90, "provider": "Alibaba"},
    "command-r-plus": {"input": 2.50, "output": 10.00, "provider": "Cohere"},
}

# Model benchmark data (example data - would be populated from real extractions)
MODEL_BENCHMARKS = {
    "gpt-4o": {
        "arena_elo": 1287,
        "mmlu": 88.7,
        "humaneval": 90.2,
        "context_window": 128000,
        "latency_ms": 800,
        "strengths": ["Reasoning", "Instruction following", "Multimodal", "Consistent performance"],
        "weaknesses": ["Higher cost tier", "Rate limits on high volume"]
    },
    "claude-3.5-sonnet": {
        "arena_elo": 1268,
        "mmlu": 88.3,
        "humaneval": 92.0,
        "context_window": 200000,
        "latency_ms": 600,
        "strengths": ["Long context handling", "Coding excellence", "Safety alignment", "Clear explanations"],
        "weaknesses": ["Occasionally verbose", "Higher output cost"]
    },
    "gemini-1.5-pro": {
        "arena_elo": 1260,
        "mmlu": 85.9,
        "humaneval": 84.1,
        "context_window": 2000000,
        "latency_ms": 900,
        "strengths": ["Massive context window (2M tokens)", "Multimodal", "Cost efficient for long docs"],
        "weaknesses": ["Slightly lower reasoning scores", "Higher latency"]
    },
    "llama-3-70b-instruct": {
        "arena_elo": 1207,
        "mmlu": 82.0,
        "humaneval": 81.7,
        "context_window": 8192,
        "latency_ms": 500,
        "strengths": ["Open source", "Very low cost", "Self-hostable", "No vendor lock-in"],
        "weaknesses": ["Shorter context window", "Lower benchmark scores than frontier"]
    },
    "deepseek-v3": {
        "arena_elo": 1275,
        "mmlu": 87.1,
        "humaneval": 86.4,
        "context_window": 64000,
        "latency_ms": 650,
        "strengths": ["Exceptional cost-to-performance ratio", "Strong reasoning", "Good coding"],
        "weaknesses": ["Newer model with less production track record"]
    },
    "gpt-4o-mini": {
        "arena_elo": 1180,
        "mmlu": 82.0,
        "humaneval": 87.0,
        "context_window": 128000,
        "latency_ms": 400,
        "strengths": ["Very low cost", "Fast responses", "Good for high-volume use"],
        "weaknesses": ["Lower quality than full GPT-4o", "Less nuanced reasoning"]
    },
    "gemini-1.5-flash": {
        "arena_elo": 1150,
        "mmlu": 78.9,
        "humaneval": 74.3,
        "context_window": 1000000,
        "latency_ms": 300,
        "strengths": ["Extremely fast", "Very low cost", "1M context window"],
        "weaknesses": ["Noticeably lower quality", "Best for simple tasks"]
    },
}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class UserRequirements:
    """Structured user requirements as defined in the spec."""
    use_case: str
    priorities: Dict[str, str]  # cost, quality, latency, context_length → low/medium/high
    monthly_budget_usd: Optional[float] = None
    expected_tokens_per_month: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserRequirements':
        return cls(
            use_case=data.get('use_case', ''),
            priorities=data.get('priorities', {}),
            monthly_budget_usd=data.get('monthly_budget_usd'),
            expected_tokens_per_month=data.get('expected_tokens_per_month')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "use_case": self.use_case,
            "priorities": self.priorities,
            "monthly_budget_usd": self.monthly_budget_usd,
            "expected_tokens_per_month": self.expected_tokens_per_month
        }


@dataclass
class CostEstimate:
    """Cost transparency structure - always shown with assumptions."""
    monthly_estimate_usd: float
    input_tokens_assumed: int
    output_tokens_assumed: int
    input_price_per_1m: float
    output_price_per_1m: float
    within_budget: Optional[bool] = None
    budget_headroom_pct: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "monthly_estimate_usd": round(self.monthly_estimate_usd, 2),
            "assumptions": {
                "input_tokens_per_month": self.input_tokens_assumed,
                "output_tokens_per_month": self.output_tokens_assumed,
                "input_price_per_1m_tokens": self.input_price_per_1m,
                "output_price_per_1m_tokens": self.output_price_per_1m
            },
            "within_budget": self.within_budget,
            "budget_headroom_pct": round(self.budget_headroom_pct, 1) if self.budget_headroom_pct else None
        }


@dataclass
class ModelRecommendation:
    """Full recommendation output as per spec."""
    recommended_model: str
    provider: str
    reasoning: str
    why_not_alternatives: List[Dict[str, str]]
    cost_estimate: CostEstimate
    caveats: List[str]
    data_freshness: str
    data_warnings: List[str]
    confidence: str  # high, medium, low
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_recommendation": {
                "model": self.recommended_model,
                "provider": self.provider,
                "confidence": self.confidence
            },
            "reasoning": self.reasoning,
            "why_not_alternatives": self.why_not_alternatives,
            "cost_estimate": self.cost_estimate.to_dict(),
            "caveats": self.caveats,
            "data_freshness": self.data_freshness,
            "data_warnings": self.data_warnings
        }


@dataclass
class DisqualificationResult:
    """Disqualifier mode output."""
    model: str
    is_recommended: bool
    disqualification_reasons: List[str]
    requirement_mismatches: List[Dict[str, str]]
    alternative_suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "is_recommended": self.is_recommended,
            "disqualification_reasons": self.disqualification_reasons,
            "requirement_mismatches": self.requirement_mismatches,
            "alternative_suggestion": self.alternative_suggestion
        }


@dataclass 
class ModelComparison:
    """Side-by-side comparison output."""
    model_a: str
    model_b: str
    verdict: str
    model_a_strengths: List[str]
    model_b_strengths: List[str]
    key_tradeoffs: List[str]
    choose_model_a_if: List[str]
    choose_model_b_if: List[str]
    benchmark_deltas: Dict[str, Dict[str, Any]]
    cost_comparison: Dict[str, Any]
    data_freshness: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "models_compared": {
                "model_a": self.model_a,
                "model_b": self.model_b
            },
            "verdict": self.verdict,
            "strengths": {
                self.model_a: self.model_a_strengths,
                self.model_b: self.model_b_strengths
            },
            "key_tradeoffs": self.key_tradeoffs,
            "choose_if": {
                self.model_a: self.choose_model_a_if,
                self.model_b: self.choose_model_b_if
            },
            "benchmark_deltas": self.benchmark_deltas,
            "cost_comparison": self.cost_comparison,
            "data_freshness": self.data_freshness
        }


# ============================================================================
# MODELSCOUT ANALYST ENGINE
# ============================================================================

class ModelScoutAnalyst:
    """
    The ModelScout AI Model Analyst.
    
    Translates benchmark data into clear, practical insights.
    Does NOT hype models.
    Explains tradeoffs, limitations, and cost implications honestly.
    """
    
    def __init__(
        self, 
        benchmark_data: Dict[str, Dict] = None,
        pricing_data: Dict[str, Dict] = None,
        data_timestamp: str = None
    ):
        self.benchmark_data = benchmark_data or MODEL_BENCHMARKS
        self.pricing_data = pricing_data or MODEL_PRICING
        self.data_timestamp = data_timestamp or datetime.utcnow().isoformat()
        
        # Initial data load from DB if available
        if DATABASE_AVAILABLE:
            try:
                self.refresh_data()
            except Exception as e:
                print(f"[WARN] Failed to refresh analyst data from DB: {e}")
    
    def _safe_float(self, val, default=0):
        """Safely convert value to float, handling strings or None."""
        try:
            if val is None: return default
            return float(val)
        except (ValueError, TypeError):
            return default

    def refresh_data(self):
        """
        Refresh benchmark and pricing data from the database.
        Merges live snapshot data with hardcoded metadata (strengths/weaknesses).
        """
        if not DATABASE_AVAILABLE:
            return
            
        db_results = get_all_latest_benchmarks()
        if not db_results:
            return

        # Map DB model names to our internal benchmark structure
        # We preserve our existing hardcoded metadata (strengths, weaknesses)
        # but override the actual scores.
        
        for db_model_id, sources in db_results.items():
            # Match DB model IDs to our internal keys
            # Handle canonical prefixes (e.g., 'openai/gpt-4o' matching 'gpt-4o')
            model_id = None
            if db_model_id in self.benchmark_data:
                model_id = db_model_id
            else:
                # Try finding a match ignoring prefixes or vice versa
                for k in self.benchmark_data.keys():
                    if db_model_id.endswith('/' + k) or k.endswith('/' + db_model_id):
                        model_id = k
                        break
            
            # If still not found, check if it's a known model we should track
            if not model_id:
                if db_model_id in self.pricing_data:
                    model_id = db_model_id
                else:
                    # Initialize new model entry if it has data
                    model_id = db_model_id
                    if model_id not in self.benchmark_data:
                        self.benchmark_data[model_id] = {
                            "strengths": ["Data recently retrieved from live benchmarks"],
                            "weaknesses": []
                        }
            
            profile = self.benchmark_data[model_id]
            
            # --- Map metrics from sources ---
            
            # 1. LMSYS Arena -> arena_elo
            if "lmsys_arena" in sources:
                arena = sources["lmsys_arena"]
                if "arena_elo" in arena:
                    profile["arena_elo"] = self._safe_float(arena["arena_elo"])
                elif "average_score" in arena:
                    profile["arena_elo"] = self._safe_float(arena["average_score"])
            
            # 2. HuggingFace -> mmlu
            if "huggingface" in sources:
                hf = sources["huggingface"]
                metrics = hf.get("metrics", hf)
                if "mmlu" in metrics:
                    profile["mmlu"] = self._safe_float(metrics["mmlu"])
                elif "average_score" in hf:
                    profile["mmlu"] = self._safe_float(hf["average_score"])
            
            # 3. LiveCodeBench -> humaneval
            if "livecodebench" in sources:
                lcb = sources["livecodebench"]
                metrics = lcb.get("metrics", lcb)
                if "humaneval" in metrics:
                    profile["humaneval"] = self._safe_float(metrics["humaneval"])
                elif "pass_at_1" in metrics:
                    profile["humaneval"] = self._safe_float(metrics["pass_at_1"])
            
            # 4. Vellum -> economics (context, latency, pricing)
            if "vellum" in sources:
                vel = sources["vellum"]
                metrics = vel.get("metrics", vel)
                
                if "context_window" in metrics:
                    profile["context_window"] = int(self._safe_float(metrics["context_window"]))
                if "latency_ms" in metrics:
                    profile["latency_ms"] = self._safe_float(metrics["latency_ms"])
                
                # Dynamic pricing override
                if "input_price" in metrics and "output_price" in metrics:
                    if model_id in self.pricing_data:
                        self.pricing_data[model_id]["input"] = self._safe_float(metrics["input_price"])
                        self.pricing_data[model_id]["output"] = self._safe_float(metrics["output_price"])

        self.data_timestamp = datetime.utcnow().isoformat()
        print(f"[OK] AI Analyst refreshed with real data for {len(db_results)} models")

    def _get_data_freshness(self) -> str:
        """Return data freshness statement."""
        try:
            ts = datetime.fromisoformat(self.data_timestamp.replace('Z', '+00:00'))
            now = datetime.utcnow()
            delta = now - ts.replace(tzinfo=None)
            
            if delta.days == 0:
                return "Benchmarks last updated today."
            elif delta.days == 1:
                return "Benchmarks last updated yesterday."
            elif delta.days < 7:
                return f"Benchmarks last updated {delta.days} days ago."
            else:
                return f"Benchmarks last updated {delta.days} days ago. Consider refreshing data."
        except:
            return f"Benchmark snapshot date: {self.data_timestamp}"
    
    def _calculate_cost(
        self, 
        model_id: str, 
        monthly_tokens: int,
        input_ratio: float = 0.75  # Assume 3:1 input:output ratio
    ) -> CostEstimate:
        """Calculate monthly cost estimate with full transparency."""
        pricing = self.pricing_data.get(model_id, {})
        
        input_price = pricing.get("input", 0)
        output_price = pricing.get("output", 0)
        
        input_tokens = int(monthly_tokens * input_ratio)
        output_tokens = int(monthly_tokens * (1 - input_ratio))
        
        input_cost = (input_tokens / 1_000_000) * input_price
        output_cost = (output_tokens / 1_000_000) * output_price
        total_cost = input_cost + output_cost
        
        return CostEstimate(
            monthly_estimate_usd=total_cost,
            input_tokens_assumed=input_tokens,
            output_tokens_assumed=output_tokens,
            input_price_per_1m=input_price,
            output_price_per_1m=output_price
        )
    
    def _score_model_fit(
        self, 
        model_id: str, 
        requirements: UserRequirements
    ) -> tuple:
        """
        Score how well a model fits user requirements.
        Returns (score, fit_reasons, disqualify_reasons)
        """
        benchmarks = self.benchmark_data.get(model_id, {})
        pricing = self.pricing_data.get(model_id, {})
        
        if not benchmarks:
            return 0, [], ["Model benchmarks not available"]
        
        score = 50  # Base score
        fit_reasons = []
        disqualify_reasons = []
        priorities = requirements.priorities
        
        # === COST PRIORITY ===
        cost_priority = priorities.get("cost", "medium").lower()
        total_price = self._safe_float(pricing.get("input", 0)) + self._safe_float(pricing.get("output", 0))
        
        if cost_priority == "low":
            if total_price < 2.0:
                score += 25
                fit_reasons.append("Low cost tier matches your budget priority")
            elif total_price < 10.0:
                score += 10
                fit_reasons.append("Moderate cost")
            else:
                score -= 15
                fit_reasons.append("Higher cost may strain budget")
        elif cost_priority == "high":
            # User is willing to pay for quality
            score += 5
            
        # === QUALITY PRIORITY ===
        quality_priority = priorities.get("quality", "medium").lower()
        arena_elo = self._safe_float(benchmarks.get("arena_elo", 0))
        
        if quality_priority == "high":
            if arena_elo >= 1270:
                score += 30
                fit_reasons.append("Top-tier reasoning quality (Arena ELO > 1270)")
            elif arena_elo >= 1220:
                score += 15
                fit_reasons.append("Strong reasoning capabilities")
            elif arena_elo < 1180:
                score -= 20
                fit_reasons.append("May not meet high quality requirements")
        elif quality_priority == "low":
            score += 5  # Don't penalize lower quality models
            
        # === LATENCY PRIORITY ===
        latency_priority = priorities.get("latency", "medium").lower()
        latency = self._safe_float(benchmarks.get("latency_ms", 1000))
        
        if latency_priority == "low":  # User wants low latency
            if latency < 400:
                score += 20
                fit_reasons.append("Very low latency for real-time applications")
            elif latency < 700:
                score += 10
                fit_reasons.append("Acceptable latency")
            elif latency > 900:
                score -= 15
                fit_reasons.append("Higher latency may impact user experience")
                
        # === CONTEXT LENGTH PRIORITY ===
        context_priority = priorities.get("context_length", "medium").lower()
        context_window = self._safe_float(benchmarks.get("context_window", 4096))
        
        if context_priority == "long":
            if context_window >= 200000:
                score += 25
                fit_reasons.append("Handles very long documents (200K+ tokens)")
            elif context_window >= 100000:
                score += 15
                fit_reasons.append("Good context length for most documents")
            elif context_window < 32000:
                score -= 20
                fit_reasons.append("Limited context may require document chunking")
                
        # === USE CASE MATCHING ===
        use_case = requirements.use_case.lower()
        
        if "code" in use_case or "programming" in use_case or "developer" in use_case:
            humaneval = self._safe_float(benchmarks.get("humaneval", 0))
            if humaneval >= 90:
                score += 15
                fit_reasons.append("Excellent coding benchmark scores")
            elif humaneval < 80:
                fit_reasons.append("Coding performance is moderate")
                
        if "document" in use_case or "analysis" in use_case or "long" in use_case:
            if context_window >= 100000:
                score += 10
                fit_reasons.append("Well-suited for document analysis")
                
        if "chat" in use_case or "conversation" in use_case:
            if latency < 500:
                score += 10
                fit_reasons.append("Fast response times for conversational use")
                
        # === BUDGET CHECK (Hard disqualification) ===
        if requirements.monthly_budget_usd and requirements.expected_tokens_per_month:
            cost_est = self._calculate_cost(model_id, requirements.expected_tokens_per_month)
            if cost_est.monthly_estimate_usd > requirements.monthly_budget_usd * 1.1:
                disqualify_reasons.append(
                    f"Exceeds budget: ~${cost_est.monthly_estimate_usd:.0f}/mo vs ${requirements.monthly_budget_usd} budget"
                )
                
        return score, fit_reasons, disqualify_reasons
    
    # =========================================================================
    # A. MODEL RECOMMENDATION EXPLANATION
    # =========================================================================
    
    def recommend(self, requirements: UserRequirements) -> ModelRecommendation:
        """
        Generate a model recommendation based on user requirements.
        
        Output structure:
        - Primary Recommendation
        - Why this model fits the user
        - Why other models were not chosen
        - Cost estimate
        - Important caveats
        """
        all_scores = {}
        disqualified = {}
        
        # Score all models
        for model_id in self.benchmark_data.keys():
            score, fit_reasons, disqualify_reasons = self._score_model_fit(model_id, requirements)
            
            if disqualify_reasons:
                disqualified[model_id] = disqualify_reasons
            else:
                all_scores[model_id] = {
                    "score": score,
                    "reasons": fit_reasons
                }
        
        if not all_scores:
            # No models qualify
            return self._no_match_recommendation(requirements, disqualified)
        
        # Rank by score
        ranked = sorted(all_scores.items(), key=lambda x: x[1]["score"], reverse=True)
        
        top_model = ranked[0][0]
        top_data = ranked[0][1]
        top_benchmarks = self.benchmark_data.get(top_model, {})
        pricing = self.pricing_data.get(top_model, {})
        
        # Build "why not" explanations for top alternatives
        why_not_alternatives = []
        for model_id, data in ranked[1:4]:
            benchmarks = self.benchmark_data.get(model_id, {})
            reasons = []
            
            # Compare to winner
            if data["score"] < top_data["score"] - 20:
                reasons.append("Significantly lower overall fit score")
            
            # Specific comparisons
            top_elo = top_benchmarks.get("arena_elo", 0)
            alt_elo = benchmarks.get("arena_elo", 0)
            if top_elo - alt_elo > 20:
                reasons.append(f"Lower reasoning scores (ELO: {alt_elo} vs {top_elo})")
                
            # Cost comparison
            alt_pricing = self.pricing_data.get(model_id, {})
            alt_total = alt_pricing.get("input", 0) + alt_pricing.get("output", 0)
            top_total = pricing.get("input", 0) + pricing.get("output", 0)
            if alt_total > top_total * 1.5:
                reasons.append("Higher cost without proportional quality gain")
                
            if not reasons:
                reasons.append("Slightly lower overall match with your requirements")
                
            why_not_alternatives.append({
                "model": model_id,
                "reasons": reasons
            })
        
        # Add disqualified models
        for model_id, reasons in list(disqualified.items())[:2]:
            why_not_alternatives.append({
                "model": model_id,
                "reasons": reasons
            })
        
        # Calculate cost
        tokens = requirements.expected_tokens_per_month or 1_000_000
        cost_estimate = self._calculate_cost(top_model, tokens)
        
        if requirements.monthly_budget_usd:
            cost_estimate.within_budget = cost_estimate.monthly_estimate_usd <= requirements.monthly_budget_usd
            if requirements.monthly_budget_usd > 0:
                cost_estimate.budget_headroom_pct = (
                    (requirements.monthly_budget_usd - cost_estimate.monthly_estimate_usd) 
                    / requirements.monthly_budget_usd * 100
                )
        
        # Build reasoning
        reasoning_parts = [
            f"This model is recommended for: {requirements.use_case}.",
        ]
        if top_data["reasons"]:
            reasoning_parts.append("Key factors: " + "; ".join(top_data["reasons"][:3]) + ".")
        if top_benchmarks.get("strengths"):
            reasoning_parts.append(f"Strengths: {', '.join(top_benchmarks['strengths'][:2])}.")
        
        # Build caveats
        caveats = []
        if top_benchmarks.get("weaknesses"):
            for weakness in top_benchmarks["weaknesses"][:2]:
                caveats.append(f"Note: {weakness}")
                
        if requirements.priorities.get("latency") == "low":
            latency = top_benchmarks.get("latency_ms", 0)
            if latency > 600:
                caveats.append("Latency may be higher than ideal for real-time applications")
        
        # Data warnings
        data_warnings = []
        if not top_benchmarks.get("arena_elo"):
            data_warnings.append("Arena ELO data unavailable for this model")
        if not top_benchmarks.get("humaneval"):
            data_warnings.append("HumanEval coding benchmark unavailable")
            
        return ModelRecommendation(
            recommended_model=top_model,
            provider=pricing.get("provider", "Unknown"),
            reasoning=" ".join(reasoning_parts),
            why_not_alternatives=why_not_alternatives,
            cost_estimate=cost_estimate,
            caveats=caveats,
            data_freshness=self._get_data_freshness(),
            data_warnings=data_warnings,
            confidence="high" if top_data["score"] > 80 else "medium" if top_data["score"] > 60 else "low"
        )
    
    def _no_match_recommendation(
        self, 
        requirements: UserRequirements, 
        disqualified: Dict[str, List[str]]
    ) -> ModelRecommendation:
        """Return when no models match requirements."""
        return ModelRecommendation(
            recommended_model="None",
            provider="N/A",
            reasoning="No models in the database meet all your specified requirements. Consider relaxing budget or quality constraints.",
            why_not_alternatives=[
                {"model": m, "reasons": r} for m, r in list(disqualified.items())[:3]
            ],
            cost_estimate=CostEstimate(0, 0, 0, 0, 0),
            caveats=["All available models were disqualified based on your constraints"],
            data_freshness=self._get_data_freshness(),
            data_warnings=["Limited model database"],
            confidence="low"
        )
    
    # =========================================================================
    # B. "WHY NOT THIS MODEL?" DISQUALIFIER MODE
    # =========================================================================
    
    def explain_disqualification(
        self, 
        model_id: str, 
        requirements: UserRequirements
    ) -> DisqualificationResult:
        """
        Explain why a specific model is not recommended.
        
        Rules:
        - Be direct but neutral
        - No subjective language
        - Focus on mismatch with requirements
        """
        if model_id not in self.benchmark_data:
            return DisqualificationResult(
                model=model_id,
                is_recommended=False,
                disqualification_reasons=["Model not found in benchmark database"],
                requirement_mismatches=[],
                alternative_suggestion=list(self.benchmark_data.keys())[0] if self.benchmark_data else None
            )
        
        score, fit_reasons, disqualify_reasons = self._score_model_fit(model_id, requirements)
        benchmarks = self.benchmark_data.get(model_id, {})
        pricing = self.pricing_data.get(model_id, {})
        
        requirement_mismatches = []
        priorities = requirements.priorities
        
        # Check each priority for mismatches
        # Cost mismatch
        if priorities.get("cost", "").lower() == "low":
            total_price = pricing.get("input", 0) + pricing.get("output", 0)
            if total_price > 10:
                requirement_mismatches.append({
                    "requirement": "Low cost priority",
                    "model_value": f"${total_price:.2f} per 1M tokens (input+output)",
                    "assessment": "Model is in the high-cost tier"
                })
        
        # Quality mismatch
        if priorities.get("quality", "").lower() == "high":
            arena_elo = benchmarks.get("arena_elo", 0)
            if arena_elo < 1220:
                requirement_mismatches.append({
                    "requirement": "High quality priority",
                    "model_value": f"Arena ELO: {arena_elo}",
                    "assessment": "Benchmark scores below top-tier threshold (1220+)"
                })
        
        # Latency mismatch
        if priorities.get("latency", "").lower() == "low":
            latency = benchmarks.get("latency_ms", 0)
            if latency > 700:
                requirement_mismatches.append({
                    "requirement": "Low latency priority",
                    "model_value": f"{latency}ms average latency",
                    "assessment": "Response time exceeds low-latency threshold (700ms)"
                })
        
        # Context mismatch
        if priorities.get("context_length", "").lower() == "long":
            context = benchmarks.get("context_window", 0)
            if context < 100000:
                requirement_mismatches.append({
                    "requirement": "Long context priority",
                    "model_value": f"{context:,} token context window",
                    "assessment": "Context window may require document chunking"
                })
        
        # Budget check
        if requirements.monthly_budget_usd and requirements.expected_tokens_per_month:
            cost_est = self._calculate_cost(model_id, requirements.expected_tokens_per_month)
            if cost_est.monthly_estimate_usd > requirements.monthly_budget_usd:
                over_by = cost_est.monthly_estimate_usd - requirements.monthly_budget_usd
                requirement_mismatches.append({
                    "requirement": f"Monthly budget: ${requirements.monthly_budget_usd}",
                    "model_value": f"Estimated: ${cost_est.monthly_estimate_usd:.0f}/month",
                    "assessment": f"Exceeds budget by ${over_by:.0f}/month"
                })
                disqualify_reasons.append(f"Budget exceeded by ${over_by:.0f}/month")
        
        # Determine if recommended
        is_recommended = score >= 60 and len(disqualify_reasons) == 0
        
        # Find alternative
        alternative = None
        if not is_recommended:
            rec = self.recommend(requirements)
            if rec.recommended_model != "None":
                alternative = rec.recommended_model
        
        return DisqualificationResult(
            model=model_id,
            is_recommended=is_recommended,
            disqualification_reasons=disqualify_reasons if disqualify_reasons else 
                ["Fit score below threshold due to priority mismatches"] if score < 60 else [],
            requirement_mismatches=requirement_mismatches,
            alternative_suggestion=alternative
        )
    
    # =========================================================================
    # C. MODEL COMPARISON MODE (SIDE-BY-SIDE)
    # =========================================================================
    
    def compare(
        self, 
        model_a: str, 
        model_b: str,
        requirements: Optional[UserRequirements] = None
    ) -> ModelComparison:
        """
        Compare two models side-by-side.
        
        Output sections:
        - High-level verdict
        - Strengths of Model A
        - Strengths of Model B
        - Key tradeoffs
        - Which user should choose which
        """
        bench_a = self.benchmark_data.get(model_a, {})
        bench_b = self.benchmark_data.get(model_b, {})
        price_a = self.pricing_data.get(model_a, {})
        price_b = self.pricing_data.get(model_b, {})
        
        if not bench_a or not bench_b:
            missing = []
            if not bench_a:
                missing.append(model_a)
            if not bench_b:
                missing.append(model_b)
            return ModelComparison(
                model_a=model_a,
                model_b=model_b,
                verdict=f"Cannot compare: benchmark data missing for {', '.join(missing)}",
                model_a_strengths=[],
                model_b_strengths=[],
                key_tradeoffs=[],
                choose_model_a_if=[],
                choose_model_b_if=[],
                benchmark_deltas={},
                cost_comparison={},
                data_freshness=self._get_data_freshness()
            )
        
        # Calculate benchmark deltas
        benchmark_deltas = {}
        
        metrics_to_compare = ["arena_elo", "mmlu", "humaneval", "context_window", "latency_ms"]
        for metric in metrics_to_compare:
            val_a = bench_a.get(metric)
            val_b = bench_b.get(metric)
            if val_a is not None and val_b is not None:
                delta = val_a - val_b
                delta_pct = (delta / val_b * 100) if val_b != 0 else 0
                benchmark_deltas[metric] = {
                    model_a: val_a,
                    model_b: val_b,
                    "delta": delta,
                    "delta_pct": round(delta_pct, 1),
                    "leader": model_a if delta > 0 else model_b if delta < 0 else "tie"
                }
        
        # Cost comparison
        total_a = price_a.get("input", 0) + price_a.get("output", 0)
        total_b = price_b.get("input", 0) + price_b.get("output", 0)
        cost_comparison = {
            model_a: {
                "input_per_1m": price_a.get("input", 0),
                "output_per_1m": price_a.get("output", 0),
                "total_per_1m": total_a
            },
            model_b: {
                "input_per_1m": price_b.get("input", 0),
                "output_per_1m": price_b.get("output", 0),
                "total_per_1m": total_b
            },
            "cheaper_model": model_a if total_a < total_b else model_b,
            "cost_difference_pct": round(abs(total_a - total_b) / max(total_a, total_b) * 100, 1) if max(total_a, total_b) > 0 else 0
        }
        
        # Build verdict
        verdict_parts = []
        
        elo_a = bench_a.get("arena_elo", 0)
        elo_b = bench_b.get("arena_elo", 0)
        elo_diff = abs(elo_a - elo_b)
        
        if elo_diff < 15:
            verdict_parts.append("Both models have comparable benchmark performance.")
        elif elo_a > elo_b:
            verdict_parts.append(f"{model_a} shows stronger benchmark scores.")
        else:
            verdict_parts.append(f"{model_b} shows stronger benchmark scores.")
        
        # Cost verdict
        if abs(total_a - total_b) / max(total_a, total_b, 0.01) > 0.5:
            cheaper = model_a if total_a < total_b else model_b
            verdict_parts.append(f"{cheaper} is significantly more cost-effective.")
        else:
            verdict_parts.append("Pricing is comparable between both models.")
        
        # Key tradeoffs
        key_tradeoffs = []
        
        if elo_a != elo_b and total_a != total_b:
            quality_leader = model_a if elo_a > elo_b else model_b
            cost_leader = model_a if total_a < total_b else model_b
            if quality_leader != cost_leader:
                key_tradeoffs.append(
                    f"{quality_leader} offers better reasoning quality, while {cost_leader} provides better cost efficiency."
                )
        
        ctx_a = bench_a.get("context_window", 0)
        ctx_b = bench_b.get("context_window", 0)
        if abs(ctx_a - ctx_b) > 50000:
            ctx_leader = model_a if ctx_a > ctx_b else model_b
            key_tradeoffs.append(
                f"{ctx_leader} provides significantly longer context ({max(ctx_a, ctx_b):,} vs {min(ctx_a, ctx_b):,} tokens)."
            )
        
        lat_a = bench_a.get("latency_ms", 1000)
        lat_b = bench_b.get("latency_ms", 1000)
        if abs(lat_a - lat_b) > 200:
            faster = model_a if lat_a < lat_b else model_b
            key_tradeoffs.append(f"{faster} offers lower latency for real-time applications.")
        
        # Choose if recommendations
        choose_a_if = []
        choose_b_if = []
        
        if elo_a > elo_b + 20:
            choose_a_if.append("You prioritize reasoning quality over cost")
        if total_a < total_b * 0.7:
            choose_a_if.append("You need to minimize costs")
        if ctx_a > ctx_b * 2:
            choose_a_if.append("You work with very long documents")
        if lat_a < lat_b - 200:
            choose_a_if.append("You need low-latency responses")
            
        if elo_b > elo_a + 20:
            choose_b_if.append("You prioritize reasoning quality over cost")
        if total_b < total_a * 0.7:
            choose_b_if.append("You need to minimize costs")
        if ctx_b > ctx_a * 2:
            choose_b_if.append("You work with very long documents")
        if lat_b < lat_a - 200:
            choose_b_if.append("You need low-latency responses")
            
        # Add strengths from benchmark data
        model_a_strengths = bench_a.get("strengths", [])
        model_b_strengths = bench_b.get("strengths", [])
        
        return ModelComparison(
            model_a=model_a,
            model_b=model_b,
            verdict=" ".join(verdict_parts),
            model_a_strengths=model_a_strengths,
            model_b_strengths=model_b_strengths,
            key_tradeoffs=key_tradeoffs,
            choose_model_a_if=choose_a_if,
            choose_model_b_if=choose_b_if,
            benchmark_deltas=benchmark_deltas,
            cost_comparison=cost_comparison,
            data_freshness=self._get_data_freshness()
        )
    
    # =========================================================================
    # D. COST TRANSPARENCY (MANDATORY)
    # =========================================================================
    
    def get_cost_breakdown(
        self, 
        model_id: str, 
        monthly_tokens: int = 1_000_000,
        input_ratio: float = 0.75
    ) -> Dict[str, Any]:
        """
        Get detailed cost breakdown for a model.
        Always includes assumptions.
        """
        pricing = self.pricing_data.get(model_id)
        if not pricing:
            return {
                "error": f"Pricing data not available for {model_id}",
                "available_models": list(self.pricing_data.keys())
            }
        
        cost_estimate = self._calculate_cost(model_id, monthly_tokens, input_ratio)
        
        return {
            "model": model_id,
            "provider": pricing.get("provider", "Unknown"),
            "cost_estimate": cost_estimate.to_dict(),
            "unit_prices": {
                "input_per_1m_tokens": pricing["input"],
                "output_per_1m_tokens": pricing["output"]
            },
            "usage_tiers": {
                "1M_tokens": self._calculate_cost(model_id, 1_000_000).monthly_estimate_usd,
                "10M_tokens": self._calculate_cost(model_id, 10_000_000).monthly_estimate_usd,
                "100M_tokens": self._calculate_cost(model_id, 100_000_000).monthly_estimate_usd,
            },
            "note": f"Cost estimates assume {int(input_ratio*100)}:{int((1-input_ratio)*100)} input:output token ratio."
        }
    
    # =========================================================================
    # E. DATA TRUST & FRESHNESS
    # =========================================================================
    
    def get_data_status(self) -> Dict[str, Any]:
        """
        Return current data status and freshness.
        """
        models_with_benchmarks = list(self.benchmark_data.keys())
        models_with_pricing = list(self.pricing_data.keys())
        
        # Check for incomplete data
        warnings = []
        for model in models_with_benchmarks:
            bench = self.benchmark_data[model]
            if not bench.get("arena_elo"):
                warnings.append(f"{model}: Arena ELO unavailable")
            if not bench.get("humaneval"):
                warnings.append(f"{model}: HumanEval benchmark unavailable")
        
        for model in models_with_benchmarks:
            if model not in models_with_pricing:
                warnings.append(f"{model}: Pricing data unavailable")
        
        return {
            "data_freshness": self._get_data_freshness(),
            "benchmark_snapshot_date": self.data_timestamp,
            "models_tracked": {
                "with_benchmarks": len(models_with_benchmarks),
                "with_pricing": len(models_with_pricing),
                "model_list": models_with_benchmarks
            },
            "data_completeness": {
                "complete": len(warnings) == 0,
                "warnings": warnings[:10],  # Limit to 10 warnings
                "total_warnings": len(warnings)
            }
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_analyst_instance = None

def get_model_scout_analyst() -> ModelScoutAnalyst:
    """Get or create the ModelScoutAnalyst singleton."""
    global _analyst_instance
    if _analyst_instance is None:
        _analyst_instance = ModelScoutAnalyst()
    return _analyst_instance


def refresh_analyst(
    benchmark_data: Dict = None, 
    pricing_data: Dict = None,
    timestamp: str = None
) -> ModelScoutAnalyst:
    """Refresh the analyst with new data."""
    global _analyst_instance
    _analyst_instance = ModelScoutAnalyst(
        benchmark_data=benchmark_data,
        pricing_data=pricing_data,
        data_timestamp=timestamp
    )
    return _analyst_instance
