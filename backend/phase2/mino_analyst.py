"""
Mino-Powered AI Analyst for Model Scout

Uses Mino.ai API to provide intelligent model recommendations
based on user requirements with structured analysis.
"""

import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Import config
try:
    from ..config import MINO_API_KEY, MINO_API_URL
except ImportError:
    try:
        import sys
        sys.path.insert(0, '..')
        from config import MINO_API_KEY, MINO_API_URL
    except:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        MINO_API_KEY = os.environ.get("MINO_API_KEY", "")
        MINO_API_URL = os.environ.get("MINO_API_URL", "https://mino.ai/v1/automation/run-sse")


@dataclass
class MinoRecommendation:
    """Mino-powered recommendation result."""
    recommended_model: str
    provider: str
    confidence: str
    reasoning: str
    cost_per_1k_input: float
    cost_per_1k_output: float
    estimated_monthly_cost: float
    within_budget: bool
    advantages: List[str]
    disadvantages: List[str]
    similar_models: List[Dict[str, Any]]
    why_better: str
    use_case_fit: str
    technical_specs: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommended_model": self.recommended_model,
            "provider": self.provider,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "cost_analysis": {
                "per_1k_input_tokens": round(self.cost_per_1k_input, 4),
                "per_1k_output_tokens": round(self.cost_per_1k_output, 4),
                "estimated_monthly_usd": round(self.estimated_monthly_cost, 2),
                "within_budget": self.within_budget
            },
            "advantages": self.advantages,
            "disadvantages": self.disadvantages,
            "similar_models": self.similar_models,
            "why_better": self.why_better,
            "use_case_fit": self.use_case_fit,
            "technical_specs": self.technical_specs
        }


class MinoAnalyst:
    """AI-powered model analyst using Mino API."""
    
    def __init__(self):
        self.api_key = MINO_API_KEY
        self.api_url = MINO_API_URL
    
    def _call_mino(self, prompt: str) -> Optional[str]:
        """Call Mino API and return the response."""
        if not self.api_key:
            print("[MinoAnalyst] No API key configured!")
            return None
        
        print(f"[MinoAnalyst] Calling Mino API...")
        
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "goal": prompt,
            "url": "https://www.google.com",
            "stream": False
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=300
            )
            
            print(f"[MinoAnalyst] Response status: {response.status_code}")
            
            if response.status_code == 200:
                # Check for SSE
                content_type = response.headers.get("Content-Type", "")
                if "text/event-stream" in content_type:
                    print("[MinoAnalyst] Parsing SSE response...")
                    # Parse data: lines
                    for line in response.text.splitlines():
                        if line.startswith("data: "):
                            data_content = line[6:].strip()
                            if data_content and data_content != "[DONE]":
                                try:
                                    # Parse the SSE event JSON
                                    if data_content.startswith("{"):
                                        event = json.loads(data_content)
                                        
                                        # Check for completion event
                                        if event.get("type") == "COMPLETE" and "resultJson" in event:
                                            print("[MinoAnalyst] Found COMPLETE event with result!")
                                            return json.dumps(event["resultJson"])
                                            
                                        # Also handle case where it might be a direct result
                                        if "recommended_model" in event:
                                            return json.dumps(event)
                                except json.JSONDecodeError:
                                    pass
                                except Exception as e:
                                    print(f"[MinoAnalyst] Error parsing SSE line: {e}")
                    
                    print("[MinoAnalyst] SSE stream finished but no COMPLETE event found.")
                    return None
                
                # Try standard JSON
                try:
                    data = response.json()
                    if "result" in data:
                        return data["result"]
                    # If it returns direct JSON structure of the answer
                    if "recommended_model" in data:
                        return json.dumps(data)
                except:
                    # Return raw text if json fails
                    return response.text

                print(f"[MinoAnalyst] No recognized result format. Keys: {list(data.keys()) if isinstance(data, dict) else 'Not dict'}")
                return None
            else:
                print(f"[MinoAnalyst] API error: {response.status_code} - {response.text[:500]}")
                return None
        except Exception as e:
            print(f"[MinoAnalyst] Request failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def recommend(
        self,
        use_case: str,
        priorities: Dict[str, str],
        monthly_budget_usd: Optional[float] = None,
        expected_tokens_per_month: Optional[int] = None
    ) -> MinoRecommendation:
        """Generate an AI-powered recommendation using Mino."""
        
        tokens = expected_tokens_per_month or 5_000_000
        budget = monthly_budget_usd or 100
        
        prompt = f"""You are an expert AI Solution Architect. 
Your goal is to recommend the SINGLE BEST AI model for a specific use case, but you must also comparison with competitors.

USER REQUIREMENTS:
- Use Case: {use_case}
- Monthly Budget: ${budget} (Keep costs UNDER this if possible)
- Expected Usage: {tokens:,} tokens/month
- Priorities: {json.dumps(priorities)}

Available Models to Consider (Analyze ALL including Open Source):
- OpenAI (GPT-4o, o1, GPT-4o-mini)
- Anthropic (Claude 3.5 Sonnet, Haiku, Opus)
- Google (Gemini 1.5 Pro/Flash, Gemini 2.0)
- Meta (Llama 3, 3.1, 3.2, 3.3)
- DeepSeek (V3, R1)
- Mistral, Qwen, Yi, etc.

CRITICAL INSTRUCTION:
Return a valid JSON object. Do not include markdown formatting (like ```json).
The JSON must follow this exact schema:

{{
  "recommended_model": "Exact Model Name",
  "provider": "Provider Name",
  "confidence": "high",
  "reasoning": "Detailed technical explanation (3-4 sentences) why this specific model beats others for this specific use case.",
  "cost_per_1m_input": 0.00,
  "cost_per_1m_output": 0.00,
  "estimated_monthly_cost": 0.00,
  "within_budget": true,
  "advantages": [
    "Advantage 1 (specific to use case)",
    "Advantage 2 (technical strength)",
    "Advantage 3",
    "Advantage 4",
    "Advantage 5"
  ],
  "disadvantages": [
    "Limitation 1",
    "Limitation 2",
    "Limitation 3"
  ],
  "similar_models": [
    {{
      "model": "Competitor 1",
      "provider": "Provider 1",
      "why_not": "Specific reason why the recommended model is better than this competitor for this use case."
    }},
    {{
      "model": "Competitor 2",
      "provider": "Provider 2",
      "why_not": "Specific reason why the recommended model is better than this competitor."
    }},
    {{
        "model": "Competitor 3",
        "provider": "Provider 3",
        "why_not": "Specific reason why the recommended model is better."
    }}
  ],
  "why_better": "A comprehensive summary comparing the recommended model against the field.",
  "use_case_fit": "Exact fit description.",
  "technical_specs": {{
    "context_window": 128000,
    "supports_streaming": true,
    "latency_estimate_ms": 500
  }}
}}
"""

        # Call Mino
        mino_response = self._call_mino(prompt)
        
        if mino_response:
            try:
                # Clean up response
                cleaned = mino_response.strip()
                
                # Remove markdown code fences if present
                if "```" in cleaned:
                    parts = cleaned.split("```")
                    if len(parts) >= 3:
                        cleaned = parts[1]
                        if cleaned.startswith("json"):
                            cleaned = cleaned[4:].strip()
                    elif len(parts) == 2:
                        cleaned = parts[1]
                        if cleaned.startswith("json"):
                            cleaned = cleaned[4:].strip()
                
                cleaned = cleaned.strip()
                print(f"[MinoAnalyst] Attempting to parse: {cleaned[:200]}...")
                
                result = json.loads(cleaned)
                print(f"[MinoAnalyst] Successfully parsed JSON!")
                
                # Calculate costs per 1K tokens
                cost_per_1k_input = result.get("cost_per_1m_input", 0) / 1000
                cost_per_1k_output = result.get("cost_per_1m_output", 0) / 1000
                
                return MinoRecommendation(
                    recommended_model=result.get("recommended_model", "Unknown"),
                    provider=result.get("provider", "Unknown"),
                    confidence=result.get("confidence", "medium"),
                    reasoning=result.get("reasoning", ""),
                    cost_per_1k_input=cost_per_1k_input,
                    cost_per_1k_output=cost_per_1k_output,
                    estimated_monthly_cost=result.get("estimated_monthly_cost", 0),
                    within_budget=result.get("within_budget", True),
                    advantages=result.get("advantages", []),
                    disadvantages=result.get("disadvantages", []),
                    similar_models=result.get("similar_models", []),
                    why_better=result.get("why_better", ""),
                    use_case_fit=result.get("use_case_fit", ""),
                    technical_specs=result.get("technical_specs", {})
                )
                
            except json.JSONDecodeError as e:
                print(f"[MinoAnalyst] JSON parse error: {e}")
                print(f"[MinoAnalyst] Full response: {mino_response}")
        
        
        # Fallback
        return self._fallback_recommendation(use_case, priorities, budget, tokens)

    def generate_benchmark_report(self, model_name: str) -> Dict[str, Any]:
        """Generate a detailed benchmark report for a specific model."""
        
        prompt = f"""You are a Lead AI Benchmark Analyst with access to all major AI leaderboards.
Generate an EXHAUSTIVE benchmark report for: {model_name}

USER DEMAND: "I need ALL the stats for {model_name} - reasoning, coding, math, safety, multilingual, EVERYTHING!"

CRITICAL REQUIREMENTS:
1. Extract MAXIMUM benchmarks (10+ metrics minimum)
2. Include ALL variants (e.g., 1.5B, 7B, 32B, 67B if they exist)
3. Compare against 5+ competitors (GPT-4o, Claude 3.5 Sonnet, Gemini 2.0, Llama 3.3, etc.)
4. Provide category breakdowns with specific scores

STRICT JSON SCHEMA (NO MARKDOWN):
{{
  "model_name": "{model_name}",
  "introduction": "Brief 2-sentence technical overview",
  "quick_stats": {{
    "overall_rank": "Top 5 globally",
    "best_category": "Mathematical Reasoning",
    "avg_score": "88.5",
    "release_date": "2025-01"
  }},
  "analysis": [
    {{ "title": "General Reasoning", "content": "...", "key_benchmarks": ["MMLU: 89.2", "GPQA: 55.1"] }},
    {{ "title": "Math & Logic", "content": "...", "key_benchmarks": ["MATH-500: 92.8", "AIME: 55.5"] }},
    {{ "title": "Coding", "content": "...", "key_benchmarks": ["HumanEval: 89.2", "LiveCodeBench: 45.3"] }},
    {{ "title": "Safety & Alignment", "content": "...", "key_benchmarks": ["TruthfulQA: 78.5"] }}
  ],
  "summary": "Executive summary highlighting dominance areas",
  "benchmarks_table": {{
    "headers": ["Model", "MMLU", "GPQA", "MATH-500", "HumanEval", "MBPP", "GSM8K", "HellaSwag", "ARC-C", "TruthfulQA", "MGSM"],
    "rows": [
      {{ "Model": "{model_name}", "MMLU": "89.2", "GPQA": "55.1", "MATH-500": "92.8", "HumanEval": "89.2", "MBPP": "82.5", "GSM8K": "94.2", "HellaSwag": "88.7", "ARC-C": "91.5", "TruthfulQA": "78.5", "MGSM": "88.9" }},
      {{ "Model": "GPT-4o", "MMLU": "88.7", "GPQA": "53.6", "MATH-500": "74.6", "HumanEval": "90.2", "MBPP": "85.7", "GSM8K": "92.0", "HellaSwag": "95.3", "ARC-C": "96.4", "TruthfulQA": "85.2", "MGSM": "90.5" }},
      {{ "Model": "Claude 3.5 Sonnet", "MMLU": "88.3", "GPQA": "59.4", "MATH-500": "78.3", "HumanEval": "92.0", "MBPP": "87.5", "GSM8K": "96.4", "HellaSwag": "89.0", "ARC-C": "96.7", "TruthfulQA": "83.3", "MGSM": "91.6" }}
    ]
  }}
}}

EXTRACT REAL DATA. If unavailable, use "N/A". Prioritize accuracy over completeness.
"""
        # Call Mino
        mino_response = self._call_mino(prompt)
        
        if mino_response:
            try:
                cleaned = mino_response.strip()
                if "```" in cleaned:
                    parts = cleaned.split("```")
                    if len(parts) >= 3:
                        cleaned = parts[1]
                        if cleaned.startswith("json"):
                           cleaned = cleaned[4:].strip()
                    elif len(parts) == 2:
                         cleaned = parts[1]
                
                cleaned = cleaned.strip()
                result = json.loads(cleaned)
                return result
            except Exception as e:
                print(f"[MinoAnalyst] Report JSON parse error: {e}")
        
        return self._fallback_benchmark_report(model_name)

    def _fallback_benchmark_report(self, model_name: str) -> Dict[str, Any]:
        return {
            "model_name": model_name,
            "introduction": f"Stats for {model_name} are primarily documented in its official technical report. This is a fallback overview.",
            "analysis": [
                {
                    "title": "General Reasoning",
                    "content": f"{model_name} demonstrates strong reasoning capabilities, comparable to top-tier closed models."
                },
                {
                    "title": "Math & Logical Thinking",
                    "content": "Shows significant performance gains in structured problem solving and mathematical proofs."
                }
            ],
            "summary": "State-of-the-art open weights model with competitive reasoning performance.",
            "benchmarks_table": {
                "headers": ["Model", "MATH", "GPQA", "HumanEval"],
                "rows": [
                    {"model": model_name, "MATH": "85.0", "GPQA": "50.0", "HumanEval": "80.0"},
                    {"model": "GPT-4o", "MATH": "90.0", "GPQA": "53.0", "HumanEval": "90.0"}
                ]
            }
        }
    
    def _fallback_recommendation(
        self,
        use_case: str,
        priorities: Dict[str, str],
        budget: float,
        tokens: int
    ) -> MinoRecommendation:
        """Fallback recommendation if Mino fails."""
        
        if priorities.get("cost") == "low":
            model = "deepseek-v3"
            provider = "DeepSeek"
            input_cost = 0.27
            output_cost = 1.10
        elif priorities.get("quality") == "high":
            model = "gpt-4o"
            provider = "OpenAI"
            input_cost = 5.00
            output_cost = 15.00
        else:
            model = "claude-3.5-sonnet"
            provider = "Anthropic"
            input_cost = 3.00
            output_cost = 15.00
        
        monthly_cost = (tokens * 0.75 / 1_000_000) * input_cost + (tokens * 0.25 / 1_000_000) * output_cost
        
        return MinoRecommendation(
            recommended_model=model,
            provider=provider,
            confidence="medium",
            reasoning=f"Selected based on {priorities.get('cost', 'balanced')} cost priority.",
            cost_per_1k_input=input_cost / 1000,
            cost_per_1k_output=output_cost / 1000,
            estimated_monthly_cost=monthly_cost,
            within_budget=monthly_cost <= budget,
            advantages=["Good balance of cost and quality"],
            disadvantages=["Fallback recommendation - limited analysis"],
            similar_models=[],
            why_better="Fallback mode active",
            use_case_fit=f"Selected for: {use_case}",
            technical_specs={"context_window": 128000, "supports_streaming": True, "latency_estimate_ms": 500}
        )


# Singleton instance
_mino_analyst = None

def get_mino_analyst() -> MinoAnalyst:
    """Get or create the MinoAnalyst singleton."""
    global _mino_analyst
    if _mino_analyst is None:
        _mino_analyst = MinoAnalyst()
    return _mino_analyst
