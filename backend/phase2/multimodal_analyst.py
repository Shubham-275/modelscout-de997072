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
    
    def _call_mino(self, prompt: str) -> Optional[str]:
        """Call Mino API and return the response."""
        if not self.api_key:
            print("[MultimodalAnalyst] No API key configured!")
            return None
        
        print(f"[MultimodalAnalyst] Calling Mino API...")
        
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
            
            print(f"[MultimodalAnalyst] Response status: {response.status_code}")
            
            if response.status_code == 200:
                # Check for SSE
                content_type = response.headers.get("Content-Type", "")
                if "text/event-stream" in content_type:
                    print("[MultimodalAnalyst] Parsing SSE response...")
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
                                            print("[MultimodalAnalyst] Found COMPLETE event with result!")
                                            return json.dumps(event["resultJson"])
                                            
                                        # Also handle case where it might be a direct result
                                        if "recommended_model" in event:
                                            return json.dumps(event)
                                except json.JSONDecodeError:
                                    pass
                                except Exception as e:
                                    print(f"[MultimodalAnalyst] Error parsing SSE line: {e}")
                    
                    print("[MultimodalAnalyst] SSE stream finished but no COMPLETE event found.")
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

                print(f"[MultimodalAnalyst] No recognized result format.")
                return None
            else:
                print(f"[MultimodalAnalyst] API error: {response.status_code} - {response.text[:500]}")
                return None
        except Exception as e:
            print(f"[MultimodalAnalyst] Request failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
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
