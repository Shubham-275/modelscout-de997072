"""
Test script for ModelScout Multimodal Analyst
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_image_recommendation():
    """Test image generation model recommendation"""
    print("\n" + "="*60)
    print("TEST 1: Image Generation Recommendation")
    print("="*60)
    
    payload = {
        "use_case": "Generate product images for e-commerce",
        "modality": "image",
        "priorities": {
            "quality": "high",
            "cost": "medium",
            "speed": "high"
        },
        "monthly_budget_usd": 100,
        "expected_usage_per_month": 1000,
        "image_requirements": {
            "min_resolution": 1024,
            "needs_safety_filter": True,
            "needs_style_diversity": True
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v2/analyst/recommend/multimodal",
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))
    
    if response.status_code == 200:
        rec = result.get("recommendation", {})
        print(f"\n✅ Recommended Model: {rec.get('recommended_model')}")
        print(f"   Provider: {rec.get('provider')}")
        print(f"   Score: {rec.get('score')}/100")
        print(f"   Confidence: {rec.get('confidence')}")
        print(f"   Reasoning: {rec.get('reasoning')}")

def test_voice_recommendation():
    """Test voice generation model recommendation"""
    print("\n" + "="*60)
    print("TEST 2: Voice Generation Recommendation")
    print("="*60)
    
    payload = {
        "use_case": "Generate podcast narration with emotions",
        "modality": "voice",
        "priorities": {
            "quality": "high",
            "cost": "medium",
            "latency": "medium"
        },
        "monthly_budget_usd": 200,
        "expected_usage_per_month": 100000,
        "voice_requirements": {
            "needs_emotions": True,
            "languages": ["en"],
            "needs_voice_cloning": False
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v2/analyst/recommend/multimodal",
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    
    if response.status_code == 200:
        rec = result.get("recommendation", {})
        print(f"\n✅ Recommended Model: {rec.get('recommended_model')}")
        print(f"   Provider: {rec.get('provider')}")
        print(f"   Score: {rec.get('score')}/100")
        print(f"   Confidence: {rec.get('confidence')}")
        print(f"   Reasoning: {rec.get('reasoning')}")
        
        benchmarks = rec.get('benchmarks', {})
        print(f"\n   Benchmarks:")
        print(f"   - Voice Naturalness: {benchmarks.get('voice_naturalness')}/100")
        print(f"   - Emotion Range: {benchmarks.get('emotion_range')}/100")
        print(f"   - Languages: {benchmarks.get('language_support')}")
        print(f"   - Latency: {benchmarks.get('latency_ms')}ms")

def test_video_recommendation():
    """Test video generation model recommendation"""
    print("\n" + "="*60)
    print("TEST 3: Video Generation Recommendation")
    print("="*60)
    
    payload = {
        "use_case": "Create short marketing videos",
        "modality": "video",
        "priorities": {
            "quality": "high",
            "cost": "low",
            "speed": "medium"
        },
        "monthly_budget_usd": 500,
        "expected_usage_per_month": 100,
        "video_requirements": {
            "min_duration_sec": 10,
            "min_resolution": "1080p"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v2/analyst/recommend/multimodal",
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        rec = result.get("recommendation", {})
        print(f"\n✅ Recommended Model: {rec.get('recommended_model')}")
        print(f"   Provider: {rec.get('provider')}")
        print(f"   Score: {rec.get('score')}/100")
        
        benchmarks = rec.get('benchmarks', {})
        print(f"\n   Benchmarks:")
        print(f"   - Video Quality: {benchmarks.get('video_quality_score')}/100")
        print(f"   - Temporal Consistency: {benchmarks.get('temporal_consistency')}/100")
        print(f"   - Max Duration: {benchmarks.get('max_duration_sec')}s")
        print(f"   - Resolution: {benchmarks.get('resolution')}")

def test_3d_recommendation():
    """Test 3D generation model recommendation"""
    print("\n" + "="*60)
    print("TEST 4: 3D Generation Recommendation")
    print("="*60)
    
    payload = {
        "use_case": "Generate game-ready 3D assets",
        "modality": "3d",
        "priorities": {
            "quality": "medium",
            "cost": "low",
            "speed": "high"
        },
        "monthly_budget_usd": 100,
        "expected_usage_per_month": 200,
        "three_d_requirements": {
            "needs_rigging": True,
            "min_polygons": 50000,
            "needs_optimization": True
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v2/analyst/recommend/multimodal",
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        rec = result.get("recommendation", {})
        print(f"\n✅ Recommended Model: {rec.get('recommended_model')}")
        print(f"   Provider: {rec.get('provider')}")
        print(f"   Score: {rec.get('score')}/100")
        
        benchmarks = rec.get('benchmarks', {})
        print(f"\n   Benchmarks:")
        print(f"   - Mesh Quality: {benchmarks.get('mesh_quality_score')}/100")
        print(f"   - Texture Quality: {benchmarks.get('texture_quality')}/100")
        print(f"   - Max Polygons: {benchmarks.get('max_polygons'):,}")
        print(f"   - Supports Rigging: {benchmarks.get('supports_rigging')}")

def test_list_multimodal_models():
    """Test listing all multimodal models"""
    print("\n" + "="*60)
    print("TEST 5: List All Multimodal Models")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/v2/analyst/models/multimodal")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nSupported Modalities: {result.get('supported_modalities')}")
        
        models_by_modality = result.get('models_by_modality', {})
        for modality, data in models_by_modality.items():
            print(f"\n{modality.upper()}: {data.get('count')} models")
            print(f"  Models: {', '.join(data.get('models', []))}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ModelScout Multimodal Analyst - Test Suite")
    print("="*60)
    
    try:
        # Test all modalities
        test_image_recommendation()
        test_voice_recommendation()
        test_video_recommendation()
        test_3d_recommendation()
        test_list_multimodal_models()
        
        print("\n" + "="*60)
        print("✅ All Tests Completed!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to backend server.")
        print("   Make sure the backend is running on http://localhost:5000")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
