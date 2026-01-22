"""
ModelScout Phase 2 - Multimodal AI Model Analyst
Extends the base analyst to support voice, video, image, and 3D generation models.

This module provides:
- Modality-specific benchmark metrics
- Dynamic scoring based on model capabilities
- Support for all AI model types (text, voice, video, image, 3D)
- Flexible recommendation engine without fixed combinations
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import json


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
# MULTIMODAL PRICING DATA
# ============================================================================

MULTIMODAL_PRICING = {
    # Image Generation Models
    "dall-e-3": {"per_image": 0.04, "provider": "OpenAI", "modality": "image"},
    "dall-e-2": {"per_image": 0.02, "provider": "OpenAI", "modality": "image"},
    "stable-diffusion-xl": {"per_image": 0.002, "provider": "Stability AI", "modality": "image"},
    "midjourney-v6": {"subscription": 30.00, "provider": "Midjourney", "modality": "image"},
    "imagen-2": {"per_image": 0.03, "provider": "Google", "modality": "image"},
    "firefly": {"credits_based": True, "provider": "Adobe", "modality": "image"},
    
    # Video Generation Models
    "runway-gen-2": {"per_second": 0.05, "provider": "Runway", "modality": "video"},
    "pika-1.0": {"subscription": 35.00, "provider": "Pika", "modality": "video"},
    "stable-video-diffusion": {"per_second": 0.01, "provider": "Stability AI", "modality": "video"},
    "sora": {"per_minute": 3.00, "provider": "OpenAI", "modality": "video"},  # Estimated
    
    # Voice/Audio Models
    "elevenlabs-turbo": {"per_1k_chars": 0.30, "provider": "ElevenLabs", "modality": "voice"},
    "elevenlabs-multilingual": {"per_1k_chars": 0.60, "provider": "ElevenLabs", "modality": "voice"},
    "openai-tts-1": {"per_1m_chars": 15.00, "provider": "OpenAI", "modality": "voice"},
    "openai-tts-1-hd": {"per_1m_chars": 30.00, "provider": "OpenAI", "modality": "voice"},
    "google-wavenet": {"per_1m_chars": 16.00, "provider": "Google", "modality": "voice"},
    "amazon-polly": {"per_1m_chars": 4.00, "provider": "Amazon", "modality": "voice"},
    "resemble-ai": {"per_1k_chars": 0.50, "provider": "Resemble AI", "modality": "voice"},
    
    # 3D Generation Models
    "meshy-3": {"per_model": 0.50, "provider": "Meshy", "modality": "3d"},
    "luma-genie": {"per_model": 1.00, "provider": "Luma AI", "modality": "3d"},
    "spline-ai": {"subscription": 20.00, "provider": "Spline", "modality": "3d"},
    "point-e": {"free": True, "provider": "OpenAI", "modality": "3d"},
}


# ============================================================================
# MULTIMODAL BENCHMARK DATA
# ============================================================================

MULTIMODAL_BENCHMARKS = {
    # Image Generation Models
    "dall-e-3": {
        "modality": "image",
        "image_quality_score": 92,  # 0-100
        "prompt_adherence": 95,
        "style_diversity": 88,
        "resolution_max": 1024,
        "generation_time_sec": 15,
        "nsfw_filter": True,
        "strengths": ["Excellent prompt following", "High quality", "Safe outputs", "Text rendering"],
        "weaknesses": ["Slower generation", "Higher cost", "Limited style control"]
    },
    "stable-diffusion-xl": {
        "modality": "image",
        "image_quality_score": 88,
        "prompt_adherence": 82,
        "style_diversity": 95,
        "resolution_max": 1024,
        "generation_time_sec": 3,
        "nsfw_filter": False,
        "strengths": ["Very fast", "Low cost", "High customization", "Open source"],
        "weaknesses": ["Requires prompt engineering", "Less consistent quality", "No built-in safety"]
    },
    "midjourney-v6": {
        "modality": "image",
        "image_quality_score": 96,
        "prompt_adherence": 90,
        "style_diversity": 98,
        "resolution_max": 2048,
        "generation_time_sec": 20,
        "nsfw_filter": True,
        "strengths": ["Exceptional artistic quality", "Best-in-class aesthetics", "Strong community"],
        "weaknesses": ["Discord-only interface", "Subscription required", "Slower generation"]
    },
    "imagen-2": {
        "modality": "image",
        "image_quality_score": 90,
        "prompt_adherence": 93,
        "style_diversity": 85,
        "resolution_max": 1024,
        "generation_time_sec": 10,
        "nsfw_filter": True,
        "strengths": ["Photorealistic outputs", "Strong prompt adherence", "Google integration"],
        "weaknesses": ["Limited availability", "Moderate cost", "Less artistic styles"]
    },
    
    # Video Generation Models
    "runway-gen-2": {
        "modality": "video",
        "video_quality_score": 85,
        "temporal_consistency": 82,
        "motion_realism": 80,
        "max_duration_sec": 16,
        "resolution": "720p",
        "fps": 24,
        "strengths": ["Good motion quality", "User-friendly", "Fast iteration"],
        "weaknesses": ["Limited duration", "Moderate cost", "Quality varies"]
    },
    "pika-1.0": {
        "modality": "video",
        "video_quality_score": 88,
        "temporal_consistency": 85,
        "motion_realism": 83,
        "max_duration_sec": 10,
        "resolution": "1080p",
        "fps": 24,
        "strengths": ["High quality", "Good consistency", "Easy to use"],
        "weaknesses": ["Short clips only", "Subscription model", "Limited control"]
    },
    "stable-video-diffusion": {
        "modality": "video",
        "video_quality_score": 80,
        "temporal_consistency": 75,
        "motion_realism": 72,
        "max_duration_sec": 4,
        "resolution": "576p",
        "fps": 24,
        "strengths": ["Open source", "Very low cost", "Customizable"],
        "weaknesses": ["Very short clips", "Lower quality", "Requires technical setup"]
    },
    "sora": {
        "modality": "video",
        "video_quality_score": 95,
        "temporal_consistency": 92,
        "motion_realism": 90,
        "max_duration_sec": 60,
        "resolution": "1080p",
        "fps": 30,
        "strengths": ["Best-in-class quality", "Long duration", "Excellent physics", "High consistency"],
        "weaknesses": ["Limited availability", "Higher cost", "Slower generation"]
    },
    
    # Voice/Audio Models
    "elevenlabs-turbo": {
        "modality": "voice",
        "voice_naturalness": 92,
        "emotion_range": 85,
        "language_support": 29,
        "latency_ms": 300,
        "voice_cloning": True,
        "strengths": ["Very natural", "Fast", "Voice cloning", "Good emotions"],
        "weaknesses": ["Moderate cost", "Occasional artifacts", "API-only"]
    },
    "elevenlabs-multilingual": {
        "modality": "voice",
        "voice_naturalness": 95,
        "emotion_range": 90,
        "language_support": 29,
        "latency_ms": 600,
        "voice_cloning": True,
        "strengths": ["Exceptional quality", "29 languages", "Best voice cloning", "Rich emotions"],
        "weaknesses": ["Higher cost", "Slower", "Requires good prompts"]
    },
    "openai-tts-1": {
        "modality": "voice",
        "voice_naturalness": 88,
        "emotion_range": 75,
        "language_support": 57,
        "latency_ms": 400,
        "voice_cloning": False,
        "strengths": ["Good quality", "Many languages", "Reliable", "OpenAI integration"],
        "weaknesses": ["No voice cloning", "Limited emotion", "Moderate cost"]
    },
    "openai-tts-1-hd": {
        "modality": "voice",
        "voice_naturalness": 93,
        "emotion_range": 82,
        "language_support": 57,
        "latency_ms": 800,
        "voice_cloning": False,
        "strengths": ["High quality", "Many languages", "Clear audio", "Consistent"],
        "weaknesses": ["Higher cost", "Slower", "No voice cloning", "Limited voices"]
    },
    "google-wavenet": {
        "modality": "voice",
        "voice_naturalness": 85,
        "emotion_range": 70,
        "language_support": 40,
        "latency_ms": 500,
        "voice_cloning": False,
        "strengths": ["Reliable", "Good language support", "GCP integration"],
        "weaknesses": ["Less natural than competitors", "Limited emotions", "Moderate cost"]
    },
    "amazon-polly": {
        "modality": "voice",
        "voice_naturalness": 80,
        "emotion_range": 65,
        "language_support": 31,
        "latency_ms": 350,
        "voice_cloning": False,
        "strengths": ["Very low cost", "Fast", "AWS integration", "Reliable"],
        "weaknesses": ["Robotic sound", "Limited emotions", "Basic quality"]
    },
    "resemble-ai": {
        "modality": "voice",
        "voice_naturalness": 90,
        "emotion_range": 88,
        "language_support": 60,
        "latency_ms": 450,
        "voice_cloning": True,
        "strengths": ["Excellent voice cloning", "Good emotions", "Many languages", "Real-time"],
        "weaknesses": ["Higher cost", "Less known", "Requires training data"]
    },
    
    # 3D Generation Models
    "meshy-3": {
        "modality": "3d",
        "mesh_quality_score": 85,
        "texture_quality": 88,
        "polygon_efficiency": 82,
        "generation_time_sec": 120,
        "max_polygons": 100000,
        "supports_rigging": True,
        "strengths": ["Good quality", "Fast generation", "Game-ready", "Texture support"],
        "weaknesses": ["Limited detail", "Moderate cost", "Topology issues"]
    },
    "luma-genie": {
        "modality": "3d",
        "mesh_quality_score": 90,
        "texture_quality": 92,
        "polygon_efficiency": 85,
        "generation_time_sec": 180,
        "max_polygons": 200000,
        "supports_rigging": False,
        "strengths": ["High quality", "Excellent textures", "Good detail", "Photorealistic"],
        "weaknesses": ["Higher cost", "Slower", "No rigging", "Large files"]
    },
    "spline-ai": {
        "modality": "3d",
        "mesh_quality_score": 78,
        "texture_quality": 75,
        "polygon_efficiency": 88,
        "generation_time_sec": 60,
        "max_polygons": 50000,
        "supports_rigging": True,
        "strengths": ["Very fast", "Web-optimized", "Easy to use", "Low poly"],
        "weaknesses": ["Lower quality", "Limited detail", "Subscription required"]
    },
    "point-e": {
        "modality": "3d",
        "mesh_quality_score": 70,
        "texture_quality": 65,
        "polygon_efficiency": 75,
        "generation_time_sec": 30,
        "max_polygons": 40000,
        "supports_rigging": False,
        "strengths": ["Free", "Open source", "Fast", "Easy to run"],
        "weaknesses": ["Lower quality", "Basic textures", "Limited control", "Experimental"]
    },
}


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
    Multimodal AI Model Analyst.
    Provides recommendations for voice, video, image, and 3D generation models.
    """
    
    def __init__(self):
        self.benchmark_data = MULTIMODAL_BENCHMARKS
        self.pricing_data = MULTIMODAL_PRICING
        self.data_timestamp = datetime.utcnow().isoformat()
    
    def _safe_float(self, val, default=0):
        """Safely convert value to float."""
        try:
            if val is None:
                return default
            return float(val)
        except (ValueError, TypeError):
            return default
    
    def _score_image_model(
        self, 
        model_id: str, 
        requirements: MultimodalRequirements
    ) -> tuple:
        """Score image generation models."""
        benchmarks = self.benchmark_data.get(model_id, {})
        pricing = self.pricing_data.get(model_id, {})
        
        if not benchmarks or benchmarks.get("modality") != "image":
            return 0, [], ["Not an image generation model"]
        
        score = 50
        fit_reasons = []
        disqualify_reasons = []
        
        # Quality priority
        quality_priority = requirements.priorities.get("quality", "medium").lower()
        image_quality = self._safe_float(benchmarks.get("image_quality_score", 0))
        
        if quality_priority == "high":
            if image_quality >= 92:
                score += 30
                fit_reasons.append("Exceptional image quality (92+ score)")
            elif image_quality >= 85:
                score += 15
                fit_reasons.append("High image quality")
            elif image_quality < 80:
                score -= 20
                fit_reasons.append("Quality may not meet high standards")
        
        # Cost priority
        cost_priority = requirements.priorities.get("cost", "medium").lower()
        per_image_cost = pricing.get("per_image", pricing.get("subscription", 999) / 1000)
        
        if cost_priority == "low":
            if per_image_cost < 0.01:
                score += 25
                fit_reasons.append("Very low cost per image")
            elif per_image_cost < 0.03:
                score += 10
                fit_reasons.append("Moderate cost")
            else:
                score -= 15
                fit_reasons.append("Higher cost tier")
        
        # Speed priority
        speed_priority = requirements.priorities.get("speed", "medium").lower()
        gen_time = self._safe_float(benchmarks.get("generation_time_sec", 30))
        
        if speed_priority == "high":
            if gen_time < 5:
                score += 20
                fit_reasons.append("Very fast generation (< 5 seconds)")
            elif gen_time < 15:
                score += 10
                fit_reasons.append("Fast generation")
            elif gen_time > 20:
                score -= 15
                fit_reasons.append("Slower generation time")
        
        # Image-specific requirements
        if requirements.image_requirements:
            # Safety filter requirement
            if requirements.image_requirements.get("needs_safety_filter"):
                if not benchmarks.get("nsfw_filter"):
                    disqualify_reasons.append("No built-in safety filter")
            
            # Resolution requirement
            min_resolution = requirements.image_requirements.get("min_resolution", 512)
            if benchmarks.get("resolution_max", 0) < min_resolution:
                disqualify_reasons.append(f"Max resolution ({benchmarks.get('resolution_max')}px) below requirement ({min_resolution}px)")
            
            # Style diversity
            if requirements.image_requirements.get("needs_style_diversity"):
                style_score = self._safe_float(benchmarks.get("style_diversity", 0))
                if style_score >= 90:
                    score += 15
                    fit_reasons.append("Excellent style diversity")
        
        # Budget check
        if requirements.monthly_budget_usd and requirements.expected_usage_per_month:
            monthly_cost = per_image_cost * requirements.expected_usage_per_month
            if monthly_cost > requirements.monthly_budget_usd * 1.1:
                disqualify_reasons.append(
                    f"Exceeds budget: ~${monthly_cost:.0f}/mo vs ${requirements.monthly_budget_usd} budget"
                )
        
        return score, fit_reasons, disqualify_reasons
    
    def _score_video_model(
        self, 
        model_id: str, 
        requirements: MultimodalRequirements
    ) -> tuple:
        """Score video generation models."""
        benchmarks = self.benchmark_data.get(model_id, {})
        pricing = self.pricing_data.get(model_id, {})
        
        if not benchmarks or benchmarks.get("modality") != "video":
            return 0, [], ["Not a video generation model"]
        
        score = 50
        fit_reasons = []
        disqualify_reasons = []
        
        # Quality priority
        quality_priority = requirements.priorities.get("quality", "medium").lower()
        video_quality = self._safe_float(benchmarks.get("video_quality_score", 0))
        temporal_consistency = self._safe_float(benchmarks.get("temporal_consistency", 0))
        
        if quality_priority == "high":
            if video_quality >= 90 and temporal_consistency >= 85:
                score += 35
                fit_reasons.append("Exceptional video quality and consistency")
            elif video_quality >= 85:
                score += 20
                fit_reasons.append("High video quality")
            elif video_quality < 80:
                score -= 20
                fit_reasons.append("Quality may not meet requirements")
        
        # Duration requirement
        if requirements.video_requirements:
            needed_duration = requirements.video_requirements.get("min_duration_sec", 5)
            max_duration = self._safe_float(benchmarks.get("max_duration_sec", 0))
            
            if max_duration < needed_duration:
                disqualify_reasons.append(
                    f"Max duration ({max_duration}s) below requirement ({needed_duration}s)"
                )
            elif max_duration >= needed_duration * 2:
                score += 15
                fit_reasons.append(f"Supports longer videos ({max_duration}s)")
            
            # Resolution requirement
            needed_res = requirements.video_requirements.get("min_resolution", "720p")
            model_res = benchmarks.get("resolution", "480p")
            res_hierarchy = {"480p": 1, "576p": 2, "720p": 3, "1080p": 4, "4k": 5}
            
            if res_hierarchy.get(model_res, 0) < res_hierarchy.get(needed_res, 3):
                score -= 15
                fit_reasons.append(f"Resolution ({model_res}) below preferred ({needed_res})")
        
        # Cost priority
        cost_priority = requirements.priorities.get("cost", "medium").lower()
        per_second_cost = pricing.get("per_second", pricing.get("subscription", 999) / 100)
        
        if cost_priority == "low":
            if per_second_cost < 0.02:
                score += 25
                fit_reasons.append("Very low cost per second")
            elif per_second_cost < 0.05:
                score += 10
                fit_reasons.append("Moderate cost")
            else:
                score -= 15
                fit_reasons.append("Higher cost tier")
        
        return score, fit_reasons, disqualify_reasons
    
    def _score_voice_model(
        self, 
        model_id: str, 
        requirements: MultimodalRequirements
    ) -> tuple:
        """Score voice/audio generation models."""
        benchmarks = self.benchmark_data.get(model_id, {})
        pricing = self.pricing_data.get(model_id, {})
        
        if not benchmarks or benchmarks.get("modality") != "voice":
            return 0, [], ["Not a voice generation model"]
        
        score = 50
        fit_reasons = []
        disqualify_reasons = []
        
        # Quality priority (naturalness)
        quality_priority = requirements.priorities.get("quality", "medium").lower()
        naturalness = self._safe_float(benchmarks.get("voice_naturalness", 0))
        
        if quality_priority == "high":
            if naturalness >= 92:
                score += 30
                fit_reasons.append("Highly natural voice quality (92+ score)")
            elif naturalness >= 85:
                score += 15
                fit_reasons.append("Good voice quality")
            elif naturalness < 80:
                score -= 20
                fit_reasons.append("Voice may sound robotic")
        
        # Voice-specific requirements
        if requirements.voice_requirements:
            # Voice cloning requirement
            if requirements.voice_requirements.get("needs_voice_cloning"):
                if benchmarks.get("voice_cloning"):
                    score += 20
                    fit_reasons.append("Supports voice cloning")
                else:
                    disqualify_reasons.append("No voice cloning support")
            
            # Language requirement
            needed_languages = requirements.voice_requirements.get("languages", [])
            supported_languages = benchmarks.get("language_support", 0)
            
            if needed_languages and len(needed_languages) > supported_languages:
                disqualify_reasons.append(
                    f"Supports {supported_languages} languages, needs {len(needed_languages)}"
                )
            elif supported_languages >= 50:
                score += 10
                fit_reasons.append(f"Extensive language support ({supported_languages} languages)")
            
            # Emotion range requirement
            if requirements.voice_requirements.get("needs_emotions"):
                emotion_range = self._safe_float(benchmarks.get("emotion_range", 0))
                if emotion_range >= 85:
                    score += 15
                    fit_reasons.append("Excellent emotional expression")
                elif emotion_range < 70:
                    score -= 10
                    fit_reasons.append("Limited emotional range")
        
        # Latency priority
        latency_priority = requirements.priorities.get("latency", "medium").lower()
        latency = self._safe_float(benchmarks.get("latency_ms", 1000))
        
        if latency_priority == "low":  # User wants low latency
            if latency < 400:
                score += 20
                fit_reasons.append("Very low latency for real-time use")
            elif latency < 600:
                score += 10
                fit_reasons.append("Acceptable latency")
            elif latency > 800:
                score -= 15
                fit_reasons.append("Higher latency may impact real-time use")
        
        # Cost priority
        cost_priority = requirements.priorities.get("cost", "medium").lower()
        per_1k_cost = pricing.get("per_1k_chars", pricing.get("per_1m_chars", 999) / 1000)
        
        if cost_priority == "low":
            if per_1k_cost < 0.20:
                score += 25
                fit_reasons.append("Very low cost per 1K characters")
            elif per_1k_cost < 0.50:
                score += 10
                fit_reasons.append("Moderate cost")
            else:
                score -= 15
                fit_reasons.append("Higher cost tier")
        
        return score, fit_reasons, disqualify_reasons
    
    def _score_3d_model(
        self, 
        model_id: str, 
        requirements: MultimodalRequirements
    ) -> tuple:
        """Score 3D generation models."""
        benchmarks = self.benchmark_data.get(model_id, {})
        pricing = self.pricing_data.get(model_id, {})
        
        if not benchmarks or benchmarks.get("modality") != "3d":
            return 0, [], ["Not a 3D generation model"]
        
        score = 50
        fit_reasons = []
        disqualify_reasons = []
        
        # Quality priority
        quality_priority = requirements.priorities.get("quality", "medium").lower()
        mesh_quality = self._safe_float(benchmarks.get("mesh_quality_score", 0))
        texture_quality = self._safe_float(benchmarks.get("texture_quality", 0))
        
        if quality_priority == "high":
            if mesh_quality >= 88 and texture_quality >= 88:
                score += 30
                fit_reasons.append("High quality meshes and textures")
            elif mesh_quality >= 80:
                score += 15
                fit_reasons.append("Good 3D quality")
            elif mesh_quality < 75:
                score -= 20
                fit_reasons.append("Quality may not meet requirements")
        
        # 3D-specific requirements
        if requirements.three_d_requirements:
            # Rigging requirement
            if requirements.three_d_requirements.get("needs_rigging"):
                if benchmarks.get("supports_rigging"):
                    score += 20
                    fit_reasons.append("Supports rigging for animation")
                else:
                    disqualify_reasons.append("No rigging support")
            
            # Polygon count requirement
            needed_polygons = requirements.three_d_requirements.get("min_polygons", 10000)
            max_polygons = self._safe_float(benchmarks.get("max_polygons", 0))
            
            if max_polygons < needed_polygons:
                disqualify_reasons.append(
                    f"Max polygons ({max_polygons:,}) below requirement ({needed_polygons:,})"
                )
            
            # Polygon efficiency (for games/real-time)
            if requirements.three_d_requirements.get("needs_optimization"):
                poly_efficiency = self._safe_float(benchmarks.get("polygon_efficiency", 0))
                if poly_efficiency >= 85:
                    score += 15
                    fit_reasons.append("Well-optimized for real-time use")
        
        # Speed priority
        speed_priority = requirements.priorities.get("speed", "medium").lower()
        gen_time = self._safe_float(benchmarks.get("generation_time_sec", 300))
        
        if speed_priority == "high":
            if gen_time < 90:
                score += 20
                fit_reasons.append("Fast 3D generation (< 90 seconds)")
            elif gen_time < 180:
                score += 10
                fit_reasons.append("Moderate generation time")
            elif gen_time > 240:
                score -= 15
                fit_reasons.append("Slower generation time")
        
        # Cost priority
        cost_priority = requirements.priorities.get("cost", "medium").lower()
        per_model_cost = pricing.get("per_model", pricing.get("subscription", 999) / 100)
        
        if cost_priority == "low":
            if per_model_cost < 0.50:
                score += 25
                fit_reasons.append("Very low cost per model")
            elif per_model_cost < 1.50:
                score += 10
                fit_reasons.append("Moderate cost")
            else:
                score -= 15
                fit_reasons.append("Higher cost tier")
        
        return score, fit_reasons, disqualify_reasons
    
    def recommend(self, requirements: MultimodalRequirements) -> Dict[str, Any]:
        """
        Generate a multimodal model recommendation.
        Dynamically scores models based on modality and requirements.
        """
        modality = requirements.modality.lower()
        all_scores = {}
        disqualified = {}
        
        # Score all models of the requested modality
        for model_id, benchmarks in self.benchmark_data.items():
            if benchmarks.get("modality") != modality:
                continue
            
            # Route to appropriate scoring function
            if modality == "image":
                score, fit_reasons, disqualify_reasons = self._score_image_model(model_id, requirements)
            elif modality == "video":
                score, fit_reasons, disqualify_reasons = self._score_video_model(model_id, requirements)
            elif modality == "voice":
                score, fit_reasons, disqualify_reasons = self._score_voice_model(model_id, requirements)
            elif modality == "3d":
                score, fit_reasons, disqualify_reasons = self._score_3d_model(model_id, requirements)
            else:
                continue
            
            if disqualify_reasons:
                disqualified[model_id] = disqualify_reasons
            else:
                all_scores[model_id] = {
                    "score": score,
                    "reasons": fit_reasons
                }
        
        if not all_scores:
            return {
                "recommended_model": "None",
                "reasoning": f"No {modality} generation models meet your requirements. Consider relaxing constraints.",
                "disqualified": disqualified,
                "confidence": "low"
            }
        
        # Rank by score
        ranked = sorted(all_scores.items(), key=lambda x: x[1]["score"], reverse=True)
        
        top_model = ranked[0][0]
        top_data = ranked[0][1]
        top_benchmarks = self.benchmark_data.get(top_model, {})
        pricing = self.pricing_data.get(top_model, {})
        
        # Build recommendation
        reasoning_parts = [
            f"This model is recommended for: {requirements.use_case}.",
        ]
        if top_data["reasons"]:
            reasoning_parts.append("Key factors: " + "; ".join(top_data["reasons"][:3]) + ".")
        if top_benchmarks.get("strengths"):
            reasoning_parts.append(f"Strengths: {', '.join(top_benchmarks['strengths'][:2])}.")
        
        # Build alternatives
        alternatives = []
        for model_id, data in ranked[1:4]:
            alternatives.append({
                "model": model_id,
                "score": data["score"],
                "reasons": data["reasons"][:2]
            })
        
        return {
            "recommended_model": top_model,
            "provider": pricing.get("provider", "Unknown"),
            "modality": modality,
            "reasoning": " ".join(reasoning_parts),
            "score": top_data["score"],
            "alternatives": alternatives,
            "disqualified": disqualified,
            "benchmarks": top_benchmarks,
            "pricing": pricing,
            "confidence": "high" if top_data["score"] > 80 else "medium" if top_data["score"] > 60 else "low",
            "data_timestamp": self.data_timestamp
        }
    
    def get_supported_modalities(self) -> List[str]:
        """Return list of supported modalities."""
        modalities = set()
        for benchmarks in self.benchmark_data.values():
            modalities.add(benchmarks.get("modality"))
        return sorted(list(modalities))
    
    def get_models_by_modality(self, modality: str) -> List[str]:
        """Get all models for a specific modality."""
        return [
            model_id 
            for model_id, benchmarks in self.benchmark_data.items()
            if benchmarks.get("modality") == modality.lower()
        ]
