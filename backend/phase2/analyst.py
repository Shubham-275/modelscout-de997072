"""
ModelScout Phase 2 - AI Analyst Module

This module implements the intelligent recommendation engine that:
- Takes structured user requirements
- Analyzes benchmark data
- Provides transparent, non-hype recommendations
- Explains tradeoffs and cost implications

CORE PRINCIPLE: Help users understand tradeoffs, not chase rankings.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


# ============================================================================
# SYSTEM PROMPT FOR AI ANALYST
# ============================================================================

ANALYST_SYSTEM_PROMPT = """
You are ModelScout, an expert AI model analyst.
Your job is to translate benchmark data into clear, practical insights for developers, startups, and decision-makers.

You do not hype models.
You explain tradeoffs, limitations, and cost implications honestly.

RULES:
- Always reference user priorities
- Always mention cost vs quality tradeoff
- Never say "best model overall"
- Be direct but neutral
- No subjective language
- Focus on mismatch with requirements when disqualifying
- No emojis, no marketing language, no absolutes ("best", "perfect", "guaranteed")

MANDATORY SECTIONS:
1. Cost estimates with assumptions stated
2. Benchmark snapshot date
3. Warning if data is incomplete

One-Line Mission: Help users make confident model decisions by understanding tradeoffs, not by chasing rankings.
"""


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class UserRequirements:
    """Structured user requirements for model recommendation."""
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


@dataclass
class ModelProfile:
    """Model data for analysis."""
    model_id: str
    provider: str
    arena_elo: Optional[float] = None
    mmlu: Optional[float] = None
    humaneval: Optional[float] = None
    input_price_per_1m: Optional[float] = None
    output_price_per_1m: Optional[float] = None
    context_length: Optional[int] = None
    latency_ms: Optional[float] = None
    strengths: List[str] = None
    weaknesses: List[str] = None
    
    def __post_init__(self):
        if self.strengths is None:
            self.strengths = []
        if self.weaknesses is None:
            self.weaknesses = []


@dataclass
class Recommendation:
    """Structured recommendation output."""
    recommended_model: str
    confidence: str  # high, medium, low
    reasoning: str
    alternatives: List[Dict[str, str]]
    cost_estimate: Dict[str, Any]
    caveats: List[str]
    disqualified_models: List[Dict[str, str]]
    data_freshness: str
    data_warnings: List[str]


# ============================================================================
# MODEL DATABASE (Phase 2 - would be populated from real data)
# ============================================================================

# Default model profiles based on common knowledge
# In production, this would be populated from benchmark snapshots
DEFAULT_MODEL_PROFILES = {
    "gpt-4o": ModelProfile(
        model_id="gpt-4o",
        provider="OpenAI",
        arena_elo=1287,
        mmlu=88.7,
        humaneval=90.2,
        input_price_per_1m=5.0,
        output_price_per_1m=15.0,
        context_length=128000,
        latency_ms=800,
        strengths=["Reasoning", "Instruction following", "Multimodal"],
        weaknesses=["Higher cost", "Rate limits"]
    ),
    "claude-3.5-sonnet": ModelProfile(
        model_id="claude-3.5-sonnet",
        provider="Anthropic",
        arena_elo=1268,
        mmlu=88.3,
        humaneval=92.0,
        input_price_per_1m=3.0,
        output_price_per_1m=15.0,
        context_length=200000,
        latency_ms=600,
        strengths=["Long context", "Coding", "Safety"],
        weaknesses=["Occasionally verbose"]
    ),
    "gemini-1.5-pro": ModelProfile(
        model_id="gemini-1.5-pro",
        provider="Google",
        arena_elo=1260,
        mmlu=85.9,
        humaneval=84.1,
        input_price_per_1m=3.5,
        output_price_per_1m=10.5,
        context_length=1000000,
        latency_ms=900,
        strengths=["Massive context", "Multimodal", "Cost efficient"],
        weaknesses=["Slightly lower reasoning scores"]
    ),
    "llama-3-70b": ModelProfile(
        model_id="llama-3-70b",
        provider="Meta",
        arena_elo=1200,
        mmlu=82.0,
        humaneval=81.7,
        input_price_per_1m=0.9,
        output_price_per_1m=0.9,
        context_length=8192,
        latency_ms=500,
        strengths=["Open source", "Very low cost", "Self-hostable"],
        weaknesses=["Shorter context", "Lower benchmark scores"]
    ),
    "deepseek-v2": ModelProfile(
        model_id="deepseek-v2",
        provider="DeepSeek",
        arena_elo=1180,
        mmlu=78.5,
        humaneval=73.8,
        input_price_per_1m=0.14,
        output_price_per_1m=0.28,
        context_length=128000,
        latency_ms=700,
        strengths=["Extremely low cost", "Good context length"],
        weaknesses=["Lower quality than frontier models"]
    ),
}


# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================

class ModelAnalyst:
    """
    The ModelScout AI Analyst.
    
    Provides intelligent model recommendations based on:
    - User requirements and priorities
    - Benchmark data
    - Cost analysis
    - Honest tradeoff assessment
    """
    
    def __init__(self, model_profiles: Dict[str, ModelProfile] = None):
        self.model_profiles = model_profiles or DEFAULT_MODEL_PROFILES
        self.last_updated = datetime.utcnow().isoformat()
    
    def analyze_requirements(self, requirements: UserRequirements) -> Recommendation:
        """
        Analyze user requirements and generate a recommendation.
        
        This is a rule-based recommendation engine. In production,
        this could be enhanced with LLM-based analysis.
        """
        scores = {}
        disqualified = []
        
        for model_id, profile in self.model_profiles.items():
            score, reasons, disqualify_reason = self._score_model(profile, requirements)
            
            if disqualify_reason:
                disqualified.append({
                    "model": model_id,
                    "reason": disqualify_reason
                })
            else:
                scores[model_id] = {
                    "score": score,
                    "reasons": reasons,
                    "profile": profile
                }
        
        if not scores:
            return self._no_recommendation_found(requirements, disqualified)
        
        # Sort by score
        ranked = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
        
        top_model_id = ranked[0][0]
        top_data = ranked[0][1]
        top_profile = top_data["profile"]
        
        # Build alternatives
        alternatives = []
        for model_id, data in ranked[1:4]:  # Top 3 alternatives
            alternatives.append({
                "model": model_id,
                "reason": f"Score: {data['score']:.1f}. " + "; ".join(data["reasons"][:2])
            })
        
        # Calculate cost estimate
        cost_estimate = self._calculate_cost(top_profile, requirements)
        
        # Build reasoning
        reasoning = self._build_reasoning(top_profile, requirements, top_data["reasons"])
        
        # Build caveats
        caveats = self._build_caveats(top_profile, requirements)
        
        # Data warnings
        data_warnings = []
        if not top_profile.arena_elo:
            data_warnings.append("Arena ELO data unavailable for this model")
        
        return Recommendation(
            recommended_model=top_model_id,
            confidence="high" if top_data["score"] > 80 else "medium" if top_data["score"] > 60 else "low",
            reasoning=reasoning,
            alternatives=alternatives,
            cost_estimate=cost_estimate,
            caveats=caveats,
            disqualified_models=disqualified,
            data_freshness=f"Benchmarks last updated: {self.last_updated}",
            data_warnings=data_warnings
        )
    
    def _score_model(
        self, 
        profile: ModelProfile, 
        requirements: UserRequirements
    ) -> tuple:
        """
        Score a model against user requirements.
        Returns (score, reasons, disqualify_reason).
        """
        score = 50  # Base score
        reasons = []
        
        priorities = requirements.priorities
        
        # Cost priority
        cost_priority = priorities.get("cost", "medium")
        if profile.input_price_per_1m is not None:
            if cost_priority == "low":  # User wants low cost
                if profile.input_price_per_1m < 1.0:
                    score += 20
                    reasons.append("Very affordable pricing")
                elif profile.input_price_per_1m < 3.0:
                    score += 10
                    reasons.append("Moderate pricing")
                else:
                    score -= 10
                    reasons.append("Higher cost")
            elif cost_priority == "high":  # User is okay with high cost for quality
                score += 5  # No penalty for expensive models
        
        # Quality priority
        quality_priority = priorities.get("quality", "medium")
        if profile.arena_elo is not None:
            if quality_priority == "high":
                if profile.arena_elo > 1250:
                    score += 25
                    reasons.append("Top-tier benchmark performance")
                elif profile.arena_elo > 1200:
                    score += 15
                    reasons.append("Strong benchmark performance")
                else:
                    score -= 5
            elif quality_priority == "low":
                score += 5  # Less weight on quality
        
        # Latency priority
        latency_priority = priorities.get("latency", "medium")
        if profile.latency_ms is not None:
            if latency_priority == "low":  # User wants low latency
                if profile.latency_ms < 500:
                    score += 15
                    reasons.append("Low latency")
                elif profile.latency_ms < 800:
                    score += 5
                elif profile.latency_ms > 1000:
                    score -= 10
                    reasons.append("Higher latency")
        
        # Context length priority
        context_priority = priorities.get("context_length", "medium")
        if profile.context_length is not None:
            if context_priority == "long":
                if profile.context_length >= 200000:
                    score += 20
                    reasons.append("Excellent context length")
                elif profile.context_length >= 100000:
                    score += 10
                    reasons.append("Good context length")
                elif profile.context_length < 32000:
                    score -= 15
                    reasons.append("Limited context length")
            elif context_priority == "short":
                score += 5  # No penalty for short context
        
        # Budget check - disqualify if over budget
        disqualify_reason = None
        if requirements.monthly_budget_usd and requirements.expected_tokens_per_month:
            estimated_cost = self._estimate_monthly_cost(
                profile, 
                requirements.expected_tokens_per_month
            )
            if estimated_cost > requirements.monthly_budget_usd * 1.2:  # 20% buffer
                disqualify_reason = f"Exceeds budget (estimated ${estimated_cost:.0f}/month vs ${requirements.monthly_budget_usd} budget)"
        
        # Use case bonus (simple keyword matching)
        use_case = requirements.use_case.lower()
        if "code" in use_case or "programming" in use_case:
            if profile.humaneval and profile.humaneval > 85:
                score += 10
                reasons.append("Strong coding performance")
        if "long" in use_case or "document" in use_case:
            if profile.context_length and profile.context_length > 100000:
                score += 10
                reasons.append("Handles long documents well")
        
        return score, reasons, disqualify_reason
    
    def _estimate_monthly_cost(self, profile: ModelProfile, tokens: int) -> float:
        """Estimate monthly cost assuming 3:1 input:output ratio."""
        if not profile.input_price_per_1m or not profile.output_price_per_1m:
            return 0
        
        input_tokens = tokens * 0.75
        output_tokens = tokens * 0.25
        
        input_cost = (input_tokens / 1_000_000) * profile.input_price_per_1m
        output_cost = (output_tokens / 1_000_000) * profile.output_price_per_1m
        
        return input_cost + output_cost
    
    def _calculate_cost(
        self, 
        profile: ModelProfile, 
        requirements: UserRequirements
    ) -> Dict[str, Any]:
        """Calculate detailed cost estimate."""
        tokens = requirements.expected_tokens_per_month or 1_000_000
        
        monthly_cost = self._estimate_monthly_cost(profile, tokens)
        
        return {
            "monthly_estimate_usd": round(monthly_cost, 2),
            "assumptions": {
                "tokens_per_month": tokens,
                "input_output_ratio": "3:1",
                "input_price_per_1m": profile.input_price_per_1m,
                "output_price_per_1m": profile.output_price_per_1m
            },
            "within_budget": (
                monthly_cost <= requirements.monthly_budget_usd 
                if requirements.monthly_budget_usd else None
            )
        }
    
    def _build_reasoning(
        self, 
        profile: ModelProfile, 
        requirements: UserRequirements,
        score_reasons: List[str]
    ) -> str:
        """Build human-readable reasoning."""
        parts = []
        
        parts.append(f"This model is recommended for your use case: {requirements.use_case}.")
        
        if score_reasons:
            parts.append("Key factors: " + "; ".join(score_reasons[:3]) + ".")
        
        if profile.strengths:
            parts.append(f"Strengths: {', '.join(profile.strengths[:2])}.")
        
        return " ".join(parts)
    
    def _build_caveats(
        self, 
        profile: ModelProfile, 
        requirements: UserRequirements
    ) -> List[str]:
        """Build list of caveats/warnings."""
        caveats = []
        
        if profile.weaknesses:
            for weakness in profile.weaknesses[:2]:
                caveats.append(f"Note: {weakness}")
        
        if requirements.priorities.get("latency") == "low" and profile.latency_ms and profile.latency_ms > 600:
            caveats.append("Latency may be higher than ideal for real-time applications")
        
        if requirements.priorities.get("context_length") == "long" and profile.context_length and profile.context_length < 100000:
            caveats.append("Context length may be limiting for very long documents")
        
        return caveats
    
    def _no_recommendation_found(
        self, 
        requirements: UserRequirements,
        disqualified: List[Dict[str, str]]
    ) -> Recommendation:
        """Return when no models match requirements."""
        return Recommendation(
            recommended_model="None",
            confidence="low",
            reasoning="No models in the database meet all your specified requirements. Consider relaxing budget or quality constraints.",
            alternatives=[],
            cost_estimate={"monthly_estimate_usd": 0, "assumptions": {}},
            caveats=["All available models were disqualified based on your constraints"],
            disqualified_models=disqualified,
            data_freshness=f"Benchmarks last updated: {self.last_updated}",
            data_warnings=["Limited model database"]
        )
    
    def compare_models(
        self, 
        model_a_id: str, 
        model_b_id: str,
        requirements: Optional[UserRequirements] = None
    ) -> Dict[str, Any]:
        """
        Compare two models side-by-side.
        
        Returns structured comparison with:
        - High-level verdict
        - Strengths of each model
        - Key tradeoffs
        - Recommendation based on use case
        """
        profile_a = self.model_profiles.get(model_a_id)
        profile_b = self.model_profiles.get(model_b_id)
        
        if not profile_a or not profile_b:
            return {
                "error": "One or both models not found in database",
                "available_models": list(self.model_profiles.keys())
            }
        
        # Calculate deltas
        deltas = {}
        if profile_a.arena_elo and profile_b.arena_elo:
            deltas["arena_elo"] = {
                "a": profile_a.arena_elo,
                "b": profile_b.arena_elo,
                "winner": model_a_id if profile_a.arena_elo > profile_b.arena_elo else model_b_id
            }
        
        if profile_a.input_price_per_1m and profile_b.input_price_per_1m:
            deltas["cost"] = {
                "a": profile_a.input_price_per_1m,
                "b": profile_b.input_price_per_1m,
                "cheaper": model_a_id if profile_a.input_price_per_1m < profile_b.input_price_per_1m else model_b_id
            }
        
        if profile_a.context_length and profile_b.context_length:
            deltas["context"] = {
                "a": profile_a.context_length,
                "b": profile_b.context_length,
                "longer": model_a_id if profile_a.context_length > profile_b.context_length else model_b_id
            }
        
        # Build verdict
        verdict = self._build_comparison_verdict(profile_a, profile_b, model_a_id, model_b_id)
        
        # Build use case recommendations
        use_case_recs = {
            "reasoning_tasks": deltas.get("arena_elo", {}).get("winner"),
            "budget_conscious": deltas.get("cost", {}).get("cheaper"),
            "long_documents": deltas.get("context", {}).get("longer"),
        }
        
        return {
            "model_a": {
                "id": model_a_id,
                "provider": profile_a.provider,
                "strengths": profile_a.strengths,
                "weaknesses": profile_a.weaknesses
            },
            "model_b": {
                "id": model_b_id,
                "provider": profile_b.provider,
                "strengths": profile_b.strengths,
                "weaknesses": profile_b.weaknesses
            },
            "deltas": deltas,
            "verdict": verdict,
            "choose_for": use_case_recs,
            "data_freshness": f"Benchmarks last updated: {self.last_updated}"
        }
    
    def _build_comparison_verdict(
        self,
        profile_a: ModelProfile,
        profile_b: ModelProfile,
        model_a_id: str,
        model_b_id: str
    ) -> str:
        """Build a nuanced comparison verdict."""
        parts = []
        
        # ELO comparison
        if profile_a.arena_elo and profile_b.arena_elo:
            elo_diff = abs(profile_a.arena_elo - profile_b.arena_elo)
            if elo_diff < 20:
                parts.append("Both models have similar benchmark performance.")
            elif profile_a.arena_elo > profile_b.arena_elo:
                parts.append(f"{model_a_id} shows stronger benchmark scores.")
            else:
                parts.append(f"{model_b_id} shows stronger benchmark scores.")
        
        # Cost comparison
        if profile_a.input_price_per_1m and profile_b.input_price_per_1m:
            cost_ratio = profile_a.input_price_per_1m / profile_b.input_price_per_1m
            if cost_ratio > 2:
                parts.append(f"{model_b_id} is significantly more cost-effective.")
            elif cost_ratio < 0.5:
                parts.append(f"{model_a_id} is significantly more cost-effective.")
            else:
                parts.append("Pricing is comparable between both models.")
        
        return " ".join(parts) if parts else "Both models are viable options depending on specific requirements."


# Singleton instance
_analyst = None

def get_analyst() -> ModelAnalyst:
    """Get or create the ModelAnalyst singleton."""
    global _analyst
    if _analyst is None:
        _analyst = ModelAnalyst()
    return _analyst
