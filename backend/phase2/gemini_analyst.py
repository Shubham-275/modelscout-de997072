"""
Gemini-Powered AI Analyst for Model Scout

This module uses Google's Gemini API to provide intelligent model recommendations
based on user requirements. Unlike the rule-based analyst, this uses AI to:
- Understand natural language requirements
- Analyze all available models dynamically
- Generate rich, contextual explanations
- Provide competitive analysis
"""

import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

# Import config for API keys
try:
    from ..config import GEMINI_API_KEY
except ImportError:
    try:
        import sys
        sys.path.insert(0, '..')
        from config import GEMINI_API_KEY
    except:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Import database utilities
try:
    from ..database import get_all_latest_benchmarks
    DATABASE_AVAILABLE = True
except ImportError:
    try:
        from database import get_all_latest_benchmarks
        DATABASE_AVAILABLE = True
    except:
        DATABASE_AVAILABLE = False


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"


# Extended model pricing database (per 1M tokens -> we'll show per 1K)
# This is our fallback; live data from Vellum will override
EXTENDED_MODEL_PRICING = {
    # OpenAI
    "gpt-4o": {"input": 5.00, "output": 15.00, "provider": "OpenAI"},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "provider": "OpenAI"},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00, "provider": "OpenAI"},
    "gpt-4": {"input": 30.00, "output": 60.00, "provider": "OpenAI"},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50, "provider": "OpenAI"},
    "o1": {"input": 15.00, "output": 60.00, "provider": "OpenAI"},
    "o1-mini": {"input": 3.00, "output": 12.00, "provider": "OpenAI"},
    
    # Anthropic
    "claude-3.5-sonnet": {"input": 3.00, "output": 15.00, "provider": "Anthropic"},
    "claude-3-opus": {"input": 15.00, "output": 75.00, "provider": "Anthropic"},
    "claude-3-sonnet": {"input": 3.00, "output": 15.00, "provider": "Anthropic"},
    "claude-3-haiku": {"input": 0.25, "output": 1.25, "provider": "Anthropic"},
    
    # Google
    "gemini-2.0-pro": {"input": 1.25, "output": 5.00, "provider": "Google"},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40, "provider": "Google"},
    "gemini-1.5-pro": {"input": 3.50, "output": 10.50, "provider": "Google"},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30, "provider": "Google"},
    
    # Meta
    "llama-3.3-70b": {"input": 0.90, "output": 0.90, "provider": "Meta"},
    "llama-3.1-405b": {"input": 3.00, "output": 3.00, "provider": "Meta"},
    "llama-3.1-70b": {"input": 0.90, "output": 0.90, "provider": "Meta"},
    "llama-3.1-8b": {"input": 0.18, "output": 0.18, "provider": "Meta"},
    "llama-3-70b-instruct": {"input": 0.90, "output": 0.90, "provider": "Meta"},
    
    # DeepSeek
    "deepseek-v3": {"input": 0.27, "output": 1.10, "provider": "DeepSeek"},
    "deepseek-v2.5": {"input": 0.14, "output": 0.28, "provider": "DeepSeek"},
    "deepseek-coder": {"input": 0.14, "output": 0.28, "provider": "DeepSeek"},
    
    # Mistral
    "mistral-large-2": {"input": 2.00, "output": 6.00, "provider": "Mistral"},
    "mistral-medium": {"input": 2.70, "output": 8.10, "provider": "Mistral"},
    "mistral-small": {"input": 0.20, "output": 0.60, "provider": "Mistral"},
    "mixtral-8x22b": {"input": 1.20, "output": 1.20, "provider": "Mistral"},
    
    # Alibaba
    "qwen2.5-72b": {"input": 0.90, "output": 0.90, "provider": "Alibaba"},
    "qwen2.5-32b": {"input": 0.50, "output": 0.50, "provider": "Alibaba"},
    "qwen2-72b-instruct": {"input": 0.90, "output": 0.90, "provider": "Alibaba"},
    
    # Cohere
    "command-r-plus": {"input": 2.50, "output": 10.00, "provider": "Cohere"},
    "command-r": {"input": 0.50, "output": 1.50, "provider": "Cohere"},
    
    # xAI
    "grok-2": {"input": 5.00, "output": 15.00, "provider": "xAI"},
    "grok-2-mini": {"input": 0.30, "output": 0.90, "provider": "xAI"},
}


@dataclass
class GeminiRecommendation:
    """Full Gemini-powered recommendation result."""
    recommended_model: str
    provider: str
    confidence: str
    reasoning: str
    cost_per_1k_input: float
    cost_per_1k_output: float
    estimated_monthly_cost: float
    strengths: List[str]
    weaknesses: List[str]
    why_better_than_alternatives: List[Dict[str, Any]]
    use_case_fit: str
    data_freshness: str
    all_models_considered: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommended_model": self.recommended_model,
            "provider": self.provider,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "cost": {
                "per_1k_input_tokens": round(self.cost_per_1k_input, 4),
                "per_1k_output_tokens": round(self.cost_per_1k_output, 4),
                "estimated_monthly_usd": round(self.estimated_monthly_cost, 2)
            },
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "why_better_than_alternatives": self.why_better_than_alternatives,
            "use_case_fit": self.use_case_fit,
            "data_freshness": self.data_freshness,
            "models_analyzed": self.all_models_considered
        }


class GeminiAnalyst:
    """
    AI-powered model analyst using Gemini API.
    Provides intelligent, context-aware recommendations.
    """
    
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.api_url = GEMINI_API_URL
        self.model_data = {}
        self.pricing_data = EXTENDED_MODEL_PRICING.copy()
        self.last_refresh = None
        self._refresh_model_data()
    
    def _refresh_model_data(self):
        """Load all available model data from the database."""
        if DATABASE_AVAILABLE:
            try:
                db_results = get_all_latest_benchmarks()
                for model_id, sources in db_results.items():
                    self.model_data[model_id] = self._parse_db_model(model_id, sources)
                self.last_refresh = datetime.utcnow()
                print(f"[GeminiAnalyst] Loaded {len(db_results)} models from database")
            except Exception as e:
                print(f"[GeminiAnalyst] DB load failed: {e}")
    
    def _parse_db_model(self, model_id: str, sources: Dict) -> Dict[str, Any]:
        """Parse database model data into a unified structure."""
        profile = {
            "model_id": model_id,
            "arena_elo": 0,
            "mmlu": 0,
            "humaneval": 0,
            "context_window": 0,
            "latency_ms": 0,
        }
        
        # Extract from various sources
        if "lmsys_arena" in sources:
            arena = sources["lmsys_arena"]
            profile["arena_elo"] = self._safe_float(arena.get("arena_elo", arena.get("average_score", 0)))
        
        if "huggingface" in sources:
            hf = sources["huggingface"]
            profile["mmlu"] = self._safe_float(hf.get("mmlu", hf.get("average_score", 0)))
        
        if "livecodebench" in sources:
            lcb = sources["livecodebench"]
            profile["humaneval"] = self._safe_float(lcb.get("humaneval", lcb.get("pass_at_1", 0)))
        
        if "vellum" in sources:
            vel = sources["vellum"]
            profile["context_window"] = int(self._safe_float(vel.get("context_window", 0)))
            profile["latency_ms"] = self._safe_float(vel.get("latency_ms", 0))
            # Update pricing if available
            if "input_price" in vel and "output_price" in vel:
                short_name = model_id.split("/")[-1] if "/" in model_id else model_id
                self.pricing_data[short_name] = {
                    "input": self._safe_float(vel["input_price"]),
                    "output": self._safe_float(vel["output_price"]),
                    "provider": model_id.split("/")[0].capitalize() if "/" in model_id else "Unknown"
                }
        
        return profile
    
    def _safe_float(self, val, default=0) -> float:
        """Safely convert to float."""
        try:
            if val is None:
                return default
            return float(val)
        except (ValueError, TypeError):
            return default
    
    def _get_all_models_context(self) -> str:
        """Build a context string with all available models and their data."""
        models_info = []
        
        # Combine DB models with pricing data
        all_model_ids = set(self.model_data.keys()) | set(self.pricing_data.keys())
        
        for model_id in all_model_ids:
            short_name = model_id.split("/")[-1] if "/" in model_id else model_id
            
            # Get benchmark data
            db_data = self.model_data.get(model_id, {})
            
            # Get pricing
            pricing = self.pricing_data.get(short_name, self.pricing_data.get(model_id, {}))
            
            info = {
                "model": short_name,
                "provider": pricing.get("provider", "Unknown"),
                "arena_elo": db_data.get("arena_elo", "N/A"),
                "mmlu": db_data.get("mmlu", "N/A"),
                "humaneval": db_data.get("humaneval", "N/A"),
                "context_window": db_data.get("context_window", "N/A"),
                "input_price_per_1m": pricing.get("input", "N/A"),
                "output_price_per_1m": pricing.get("output", "N/A"),
            }
            models_info.append(info)
        
        return json.dumps(models_info, indent=2)
    
    def _call_gemini(self, prompt: str) -> Optional[str]:
        """Call Gemini API and return the response text."""
        if not self.api_key:
            print("[GeminiAnalyst] No API key configured!")
            return None
        
        print(f"[GeminiAnalyst] Calling Gemini API...")
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 4096
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            print(f"[GeminiAnalyst] Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if "candidates" in data and len(data["candidates"]) > 0:
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"[GeminiAnalyst] Got response of {len(text)} chars")
                    return text
                else:
                    print(f"[GeminiAnalyst] No candidates in response")
            else:
                print(f"[GeminiAnalyst] API error: {response.status_code} - {response.text[:200]}")
                return None
        except Exception as e:
            print(f"[GeminiAnalyst] Request failed: {e}")
            return None
    
    def recommend(
        self,
        use_case: str,
        priorities: Dict[str, str],
        monthly_budget_usd: Optional[float] = None,
        expected_tokens_per_month: Optional[int] = None
    ) -> GeminiRecommendation:
        """
        Generate an AI-powered recommendation using Gemini.
        
        Args:
            use_case: Text description of what the user wants to build
            priorities: Dict with cost, quality, latency, context_length priorities
            monthly_budget_usd: Optional budget constraint
            expected_tokens_per_month: Expected usage
        """
        # Refresh data if stale
        if not self.last_refresh or (datetime.utcnow() - self.last_refresh).seconds > 300:
            self._refresh_model_data()
        
        models_context = self._get_all_models_context()
        tokens = expected_tokens_per_month or 1_000_000
        
        prompt = f"""Recommend the best AI model for this use case.

User needs: {use_case}
Budget: ${monthly_budget_usd if monthly_budget_usd else 'unlimited'}/month for {tokens:,} tokens
Priorities: Cost={priorities.get('cost', 'medium')}, Quality={priorities.get('quality', 'medium')}

Available models with pricing (per 1M tokens):
{models_context}

Return ONLY valid JSON (no markdown):
{{
    "recommended_model": "model-name",
    "provider": "Provider",
    "confidence": "high",
    "reasoning": "Brief why this is best",
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1"],
    "use_case_fit": "How it fits",
    "alternatives_comparison": [{{"model": "alt1", "why_not": "reason"}}]
}}"""

        # Call Gemini
        gemini_response = self._call_gemini(prompt)
        
        if gemini_response:
            try:
                # Clean up response (remove markdown code blocks if present)
                cleaned = gemini_response.strip()
                
                # Remove markdown code fences
                if "```" in cleaned:
                    # Extract content between first and last ```
                    parts = cleaned.split("```")
                    if len(parts) >= 3:
                        cleaned = parts[1]
                        # Remove language identifier if present
                        if cleaned.startswith("json"):
                            cleaned = cleaned[4:].strip()
                    elif len(parts) == 2:
                        # Only opening fence, take everything after it
                        cleaned = parts[1]
                        if cleaned.startswith("json"):
                            cleaned = cleaned[4:].strip()
                
                cleaned = cleaned.strip()
                print(f"[GeminiAnalyst] Attempting to parse: {cleaned[:200]}...")
                
                result = json.loads(cleaned)
                print(f"[GeminiAnalyst] Successfully parsed JSON!")
                
                # Get pricing for recommended model
                rec_model = result.get("recommended_model", "")
                pricing = self.pricing_data.get(rec_model, {"input": 0, "output": 0, "provider": "Unknown"})
                
                # Calculate costs (per 1K tokens = per 1M tokens / 1000)
                cost_per_1k_input = pricing.get("input", 0) / 1000
                cost_per_1k_output = pricing.get("output", 0) / 1000
                
                # Estimate monthly cost (assume 75% input, 25% output)
                input_tokens = tokens * 0.75
                output_tokens = tokens * 0.25
                monthly_cost = (input_tokens / 1_000_000) * pricing.get("input", 0) + \
                               (output_tokens / 1_000_000) * pricing.get("output", 0)
                
                return GeminiRecommendation(
                    recommended_model=result.get("recommended_model", "Unknown"),
                    provider=result.get("provider", pricing.get("provider", "Unknown")),
                    confidence=result.get("confidence", "medium"),
                    reasoning=result.get("reasoning", ""),
                    cost_per_1k_input=cost_per_1k_input,
                    cost_per_1k_output=cost_per_1k_output,
                    estimated_monthly_cost=monthly_cost,
                    strengths=result.get("strengths", []),
                    weaknesses=result.get("weaknesses", []),
                    why_better_than_alternatives=result.get("alternatives_comparison", []),
                    use_case_fit=result.get("use_case_fit", ""),
                    data_freshness=f"Data refreshed at {self.last_refresh.isoformat() if self.last_refresh else 'N/A'}",
                    all_models_considered=len(set(self.model_data.keys()) | set(self.pricing_data.keys()))
                )
                
            except json.JSONDecodeError as e:
                print(f"[GeminiAnalyst] JSON parse error: {e}")
                print(f"[GeminiAnalyst] Full response ({len(gemini_response)} chars): {gemini_response}")
        
        # Fallback to rule-based if Gemini fails
        return self._fallback_recommendation(use_case, priorities, monthly_budget_usd, tokens)
    
    def _fallback_recommendation(
        self,
        use_case: str,
        priorities: Dict[str, str],
        budget: Optional[float],
        tokens: int
    ) -> GeminiRecommendation:
        """Fallback to rule-based recommendation if Gemini fails."""
        
        # Simple logic: pick based on cost priority
        if priorities.get("cost") == "low":
            model = "deepseek-v3"
        elif priorities.get("quality") == "high":
            model = "gpt-4o"
        else:
            model = "claude-3.5-sonnet"
        
        pricing = self.pricing_data.get(model, {"input": 1, "output": 3, "provider": "Unknown"})
        
        input_tokens = tokens * 0.75
        output_tokens = tokens * 0.25
        monthly_cost = (input_tokens / 1_000_000) * pricing.get("input", 0) + \
                       (output_tokens / 1_000_000) * pricing.get("output", 0)
        
        return GeminiRecommendation(
            recommended_model=model,
            provider=pricing.get("provider", "Unknown"),
            confidence="medium",
            reasoning=f"Based on your {priorities.get('cost', 'balanced')} cost priority and {priorities.get('quality', 'medium')} quality needs.",
            cost_per_1k_input=pricing.get("input", 0) / 1000,
            cost_per_1k_output=pricing.get("output", 0) / 1000,
            estimated_monthly_cost=monthly_cost,
            strengths=["Good balance of cost and quality"],
            weaknesses=["Recommendation based on rules, not AI analysis"],
            why_better_than_alternatives=[],
            use_case_fit=f"Selected for: {use_case}",
            data_freshness="Fallback mode - limited data",
            all_models_considered=len(self.pricing_data)
        )


# Singleton instance
_gemini_analyst = None

def get_gemini_analyst() -> GeminiAnalyst:
    """Get or create the GeminiAnalyst singleton."""
    global _gemini_analyst
    if _gemini_analyst is None:
        _gemini_analyst = GeminiAnalyst()
    return _gemini_analyst
