"""
ModelScout Phase 2 - Multimodal AI Model Analyst
Extends the base analyst to support voice, video, image, and 3D generation models.

This module provides:
- Modality-specific benchmark metrics via Mino API
- Dynamic scoring based on model capabilities
- Support for all AI model types (text, voice, video, image, 3D)
- Flexible recommendation engine without hardcoded data
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import json
import requests

# Import Mino API configuration
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


# ============================================================================
# MODALITY DEFINITIONS
# ============================================================================

class ModelModality(Enum):
    """Supported model modalities."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    VOICE = "voice"
    AUDIO = "audio"
    THREE_D = "3d"
    MULTIMODAL = "multimodal"


# ============================================================================
# MULTIMODAL ANALYST ENGINE
# ============================================================================

@dataclass
class MultimodalRequirements:
    """User requirements for multimodal models."""
    use_case: str
    modality: str  # "image", "video", "voice", "3d"
    priorities: Dict[str, str]  # quality, cost, speed, etc.
    monthly_budget_usd: Optional[float] = None
    expected_usage_per_month: Optional[int] = None  # images, seconds, characters, models
    
    # Modality-specific requirements
    image_requirements: Optional[Dict[str, Any]] = None  # resolution, style, safety
    video_requirements: Optional[Dict[str, Any]] = None  # duration, fps, resolution
    voice_requirements: Optional[Dict[str, Any]] = None  # languages, emotions, cloning
    three_d_requirements: Optional[Dict[str, Any]] = None  # polygons, rigging, format
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MultimodalRequirements':
        return cls(
            use_case=data.get('use_case', ''),
            modality=data.get('modality', 'text'),
            priorities=data.get('priorities', {}),
            monthly_budget_usd=data.get('monthly_budget_usd'),
            expected_usage_per_month=data.get('expected_usage_per_month'),
            image_requirements=data.get('image_requirements'),
            video_requirements=data.get('video_requirements'),
            voice_requirements=data.get('voice_requirements'),
            three_d_requirements=data.get('three_d_requirements')
        )


class MultimodalAnalyst:
    """
    Multimodal AI Model Analyst - Mino API Powered.
    Provides dynamic recommendations for voice, video, image, and 3D generation models.
    Uses Mino API to discover and analyze models instead of hardcoded data.
    """
    
    def __init__(self):
        self.api_key = MINO_API_KEY
        self.api_url = MINO_API_URL
        self.data_timestamp = datetime.utcnow().isoformat()
    
    def _call_mino(self, prompt: str, url: str = "https://www.google.com") -> Optional[str]:
        """Call Mino API and return the response."""
        if not self.api_key:
            return None
        
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "goal": prompt,
            "url": url,
            "stream": False
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=300
            )
            
            if response.status_code == 200:
                # Check for SSE
                content_type = response.headers.get("Content-Type", "")
                if "text/event-stream" in content_type:
                    # Parse data: lines
                    for line in response.text.splitlines():
                        if line.startswith("data: "):
                            data_content = line[6:].strip()
                            if data_content and data_content != "[DONE]":
                                try:
                                    if data_content.startswith("{"):
                                        event = json.loads(data_content)
                                        # Check for completion event
                                        if event.get("type") == "COMPLETE" and "resultJson" in event:
                                            return json.dumps(event["resultJson"])
                                        # Also handle case where it might be a direct result
                                        if "recommended_model" in event:
                                            return json.dumps(event)
                                except:
                                    pass
                    return None
                
                # Try standard JSON
                try:
                    data = response.json()
                    if "result" in data:
                        return data["result"]
                    if "recommended_model" in data:
                        return json.dumps(data)
                except:
                    return response.text
                return None
            else:
                return None
        except Exception as e:
            print(f"[MultimodalAnalyst] Request failed: {e}")
            return None

    def _run_parallel_scouts(self, scouts: List[Dict[str, str]]) -> Any:
        """
        Run multiple Mino agents in parallel threads and yield logs/results from a queue.
        """
        import concurrent.futures
        import queue
        
        q = queue.Queue()
        
        def run_scout(scout):
            name = scout["name"]
            prompt = scout["prompt"]
            target_url = scout.get("url", "https://www.bing.com")
            
            try:
                q.put({"type": "log", "message": f"[{name}] Searching {target_url}..."})
                response = self._call_mino(prompt, url=target_url)
                q.put({"type": "log", "message": f"[{name}] Analysis complete."})
                return {"name": name, "data": response}
            except Exception as e:
                q.put({"type": "error", "message": f"[{name}] Failed: {str(e)}"})
                return {"name": name, "error": str(e)}

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(scouts)) as executor:
            futures = {executor.submit(run_scout, s): s for s in scouts}
            
            while True:
                try:
                    while True:
                        msg = q.get_nowait()
                        yield msg
                except queue.Empty:
                    pass
                
                if all(f.done() for f in futures):
                    break
                
                import time
                time.sleep(0.1)
            
            results = {}
            for f in concurrent.futures.as_completed(futures):
                res = f.result()
                if "data" in res and res["data"]:
                    results[res["name"]] = res["data"]
            
            yield {"type": "internal_complete", "data": results}
    
    
    def recommend(self, requirements: MultimodalRequirements) -> Dict[str, Any]:
        """
        Generate a multimodal model recommendation using Mino API.
        Dynamically discovers and analyzes models based on modality and requirements.
        """
        modality = requirements.modality.lower()
        use_case = requirements.use_case
        priorities = requirements.priorities
        budget = requirements.monthly_budget_usd or 1000
        usage = requirements.expected_usage_per_month or 1000
        
        # Build modality-specific context
        modality_context = ""
        if modality == "image":
            modality_context = f"""
MODALITY: IMAGE GENERATION
User Requirements: {json.dumps(requirements.image_requirements) if requirements.image_requirements else 'None specified'}
Expected Usage: {usage} images per month
Pricing Unit: per image or subscription
Key Metrics: image quality, prompt adherence, style diversity, resolution, generation time, safety filters
"""
        elif modality == "video":
            modality_context = f"""
MODALITY: VIDEO GENERATION
User Requirements: {json.dumps(requirements.video_requirements) if requirements.video_requirements else 'None specified'}
Expected Usage: {usage} seconds of video per month
Pricing Unit: per second, per minute, or subscription
Key Metrics: video quality, temporal consistency, motion realism, max duration, resolution, FPS
"""
        elif modality == "voice":
            modality_context = f"""
MODALITY: VOICE/AUDIO GENERATION
User Requirements: {json.dumps(requirements.voice_requirements) if requirements.voice_requirements else 'None specified'}
Expected Usage: {usage} characters per month
Pricing Unit: per 1K characters or per 1M characters
Key Metrics: voice naturalness, emotion range, language support, latency, voice cloning capability
"""
        elif modality == "3d":
            modality_context = f"""
MODALITY: 3D MODEL GENERATION
User Requirements: {json.dumps(requirements.three_d_requirements) if requirements.three_d_requirements else 'None specified'}
Expected Usage: {usage} 3D models per month
Pricing Unit: per model or subscription
Key Metrics: mesh quality, texture quality, polygon efficiency, generation time, rigging support
"""
        else:
            return {
                "recommended_model": "None",
                "reasoning": f"Unsupported modality: {modality}",
                "confidence": "low"
            }
        
        # Build Mino prompt
        prompt = f"""You are an expert AI Model Analyst specializing in {modality.upper()} GENERATION models.

{modality_context}

USER REQUIREMENTS:
- Use Case: {use_case}
- Monthly Budget: ${budget}
- Expected Usage: {usage} units/month
- Priorities: {json.dumps(priorities)}

YOUR TASK:
1. Research and identify ALL available {modality} generation models (including latest releases from 2024-2026)
2. Compare their pricing, performance benchmarks, and capabilities
3. Recommend the SINGLE BEST model for this specific use case
4. Provide 2-3 alternative options with reasons why they weren't chosen

CRITICAL: Return ONLY valid JSON (no markdown formatting). Use this exact schema:

{{
  "recommended_model": "Exact Model Name",
  "provider": "Provider Name",
  "modality": "{modality}",
  "confidence": "high",
  "reasoning": "Detailed explanation (3-4 sentences) why this model is best for the use case.",
  "pricing": {{
    "per_image": 0.00,
    "per_second": 0.00,
    "per_1k_chars": 0.00,
    "per_model": 0.00,
    "subscription": 0.00,
    "provider": "Provider Name"
  }},
  "benchmarks": {{
    "strengths": ["Strength 1", "Strength 2", "Strength 3"],
    "weaknesses": ["Weakness 1", "Weakness 2"],
    "quality_score": 90,
    "specific_metrics": {{}}
  }},
  "alternatives": [
    {{
      "model": "Alternative 1",
      "provider": "Provider",
      "reasons": ["Why not chosen reason 1", "Why not chosen reason 2"]
    }},
    {{
      "model": "Alternative 2",
      "provider": "Provider",
      "reasons": ["Why not chosen"]
    }}
  ],
  "estimated_monthly_cost": 0.00,
  "within_budget": true
}}

Research the latest models and provide accurate, up-to-date information."""

        # Call Mino API
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
                print(f"[MultimodalAnalyst] Attempting to parse: {cleaned[:200]}...")
                
                result = json.loads(cleaned)
                print(f"[MultimodalAnalyst] Successfully parsed JSON!")
                
                # Add timestamp
                result["data_timestamp"] = self.data_timestamp
                
                return result
                
            except json.JSONDecodeError as e:
                print(f"[MultimodalAnalyst] JSON parse error: {e}")
                print(f"[MultimodalAnalyst] Full response: {mino_response}")
        
        # Fallback
        return self._fallback_recommendation(modality, use_case, budget)
    
    def recommend_stream(self, requirements: MultimodalRequirements):
        """
        Generate a multimodal model recommendation with streaming logs using Functional Squads.
        """
        modality = requirements.modality.lower()
        use_case = requirements.use_case
        priorities = requirements.priorities
        budget = requirements.monthly_budget_usd or 1000
        usage = requirements.expected_usage_per_month or 1000

        yield {"type": "log", "message": f"Initializing Functional Squad for {modality.upper()} recommendation..."}
        
        # 1. Define Scouts based on Modality
        scouts = []
        if modality == "image":
            scouts = [
                {
                    "name": "Quality Analyst",
                    "url": "https://www.bing.com/search?q=best+image+generation+models+2025+benchmark+quality",
                    "prompt": f"Identify top 3 image models for '{use_case}'. focus on visual quality (FID, realism). Return JSON summary."
                },
                {
                    "name": "Pricing Analyst",
                    "url": "https://www.bing.com/search?q=ai+image+generator+pricing+comparison+2025",
                    "prompt": f"Find pricing for top image models (Midjourney, DALL-E 3, Flux, Adobe Firefly). Cost per image? Subscription? Return JSON."
                },
                {
                    "name": "Review Analyst",
                    "url": "https://www.bing.com/search?q=reddit+stable+diffusion+vs+midjourney+v6+review",
                    "prompt": f"Find user consensus on Midjourney vs Stable Diffusion vs Flux. Pros/Cons for '{use_case}'. Return JSON."
                }
            ]
        elif modality == "video":
            scouts = [
                {
                    "name": "Motion Analyst",
                    "url": "https://www.bing.com/search?q=best+ai+video+generator+2025+temporal+consistency",
                    "prompt": f"Identify top video models (Sora, Runway Gen-3, Pika, Luma). Focus on motion smoothness and consistency. Return JSON."
                },
                {
                    "name": "Tech Analyst",
                    "url": "https://www.bing.com/search?q=ai+video+generation+max+duration+resolution+comparison",
                    "prompt": f"Compare specs: Max duration, Resolution (1080p/4K), FBS. Return JSON."
                },
                {
                    "name": "Pricing Analyst",
                    "url": "https://www.bing.com/search?q=runway+ml+pricing+vs+pika+labs+subscription+cost",
                    "prompt": f"Find pricing models for Runway, Pika, Luma. Cost per second? Return JSON."
                }
            ]
        elif modality == "voice":
            scouts = [
                {
                    "name": "Audio Analyst",
                    "url": "https://www.bing.com/search?q=best+ai+voice+cloning+model+2025+quality",
                    "prompt": f"Identify top voice models (ElevenLabs, OpenAI, PlayHT). Focus on realism and cloning speed. Return JSON."
                },
                {
                    "name": "Feature Analyst",
                    "url": "https://www.bing.com/search?q=elevenlabs+vs+playht+features+emotions+latency",
                    "prompt": f"Compare features: Emotional control, low latency (real-time), language support. Return JSON."
                },
                {
                    "name": "Cost Analyst",
                    "url": "https://www.bing.com/search?q=ai+tts+pricing+comparison+per+character",
                    "prompt": f"Compare pricing for ElevenLabs, Azure, OpenAI. Cost per 1k chars? Return JSON."
                }
            ]
        elif modality == "3d":
            scouts = [
                {
                    "name": "Mesh Analyst",
                    "url": "https://www.bing.com/search?q=best+ai+3d+model+generator+2025+topology",
                    "prompt": f"Identify top 3D models (Meshy, Luma Genie, Rodin). Focus on mesh topology and UV quality. Return JSON."
                },
                {
                    "name": "Speed Analyst",
                    "url": "https://www.bing.com/search?q=fastest+ai+3d+asset+generator+benchmark",
                    "prompt": f"Compare generation speed. Which tools are distinctively faster? Return JSON."
                },
                {
                    "name": "Integration Analyst",
                    "url": "https://www.bing.com/search?q=ai+3d+model+generator+game+engine+workflow+compatibility",
                    "prompt": f"Check compatibility with Unity/Unreal/Blender. Export formats (GLB, OBJ, FBX). Return JSON."
                }
            ]
        else:
             yield {"type": "error", "message": f"Unsupported modality: {modality}"}
             return

        scout_results = {}
        results_text = ""
        
        # 2. Run Parallel Scouts
        for event in self._run_parallel_scouts(scouts):
             if event.get("type") == "log":
                 yield event
             elif event.get("type") == "internal_complete":
                 scout_results = event.get("data", {})
        
        # Format for Aggregator
        for name, data in scout_results.items():
             results_text += f"\n--- REPORT FROM {name} ---\n{data}\n"
        
        if not results_text:
             yield {"type": "log", "message": "Scouts failed to return data. Using fallback."}
             fallback = self._fallback_recommendation(modality, use_case, budget)
             yield {"type": "result", "data": fallback}
             return

        # 3. Final Synthesis
        yield {"type": "log", "message": "Synthesizing intelligence to formulate recommendation..."}
        
        aggregator_prompt = f"""You are the Lead Solutions Architect.
Synthesize the following research reports to recommend the BEST {modality} model for this user.

USER REQUIREMENTS:
- Use Case: {use_case}
- Budget: ${budget}
- Usage: {usage} units/mo
- Priorities: {json.dumps(priorities)}

RESEARCH REPORTS:
{results_text}

Calculate the estimated monthly cost based on the Pricing Analyst report and Usage.

Return ONLY valid JSON:
{{
  "recommended_model": "Exact Model Name",
  "provider": "Provider Name",
  "modality": "{modality}",
  "confidence": "high",
  "reasoning": "Detailed explanation...",
  "pricing": {{
    "per_unit": 0.00,
    "subscription": 0.00,
    "details": "..."
  }},
  "benchmarks": {{
    "strengths": ["..."],
    "weaknesses": ["..."],
    "quality_score": 90,
    "specific_metrics": {{}}
  }},
  "alternatives": [
    {{ "model": "Alt 1", "reasons": ["..."] }}
  ],
  "estimated_monthly_cost": 0.00,
  "within_budget": true,
  "sources": ["Bing", "Reddit"]
}}
"""
        final_response = self._call_mino(aggregator_prompt, url="https://www.google.com")
        
        if final_response:
            try:
                cleaned = final_response.strip()
                if "```" in cleaned:
                    parts = cleaned.split("```")
                    if len(parts) >= 2:
                        cleaned = parts[1]
                        if cleaned.startswith("json"):
                             cleaned = cleaned[4:].strip()
                
                final_data = json.loads(cleaned)
                yield {"type": "result", "data": final_data}
            except Exception as e:
                yield {"type": "error", "message": f"Synthesis failed: {e}"}
        else:
             yield {"type": "error", "message": "Synthesis returned empty response."}

    def _fallback_recommendation(self, modality: str, use_case: str, budget: float) -> Dict[str, Any]:
        """Fallback recommendation if Mino API fails."""
        return {
            "recommended_model": f"Unable to fetch {modality} models",
            "provider": "Unknown",
            "modality": modality,
            "confidence": "low",
            "reasoning": f"Mino API unavailable. Please try again or check your API key. Use case: {use_case}",
            "pricing": {},
            "benchmarks": {
                "strengths": [],
                "weaknesses": ["API unavailable"],
                "quality_score": 0
            },
            "alternatives": [],
            "estimated_monthly_cost": 0,
            "within_budget": False,
            "data_timestamp": self.data_timestamp
        }
    
    def get_supported_modalities(self) -> List[str]:
        """Return list of supported modalities."""
        return ["image", "video", "voice", "3d"]
    
    def get_models_by_modality(self, modality: str) -> List[str]:
        """
        Get all models for a specific modality via Mino API.
        Note: This requires a Mino API call and returns discovered models.
        """
        prompt = f"""List all available {modality} generation AI models currently on the market.
Return as JSON array: ["model1", "model2", "model3", ...]"""
        
        response = self._call_mino(prompt)
        if response:
            try:
                return json.loads(response)
            except:
                pass
        return []
