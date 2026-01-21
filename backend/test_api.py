import requests
import json

url = "http://localhost:5000/api/v2/analyst/recommend"
payload = {
    "use_case": "python code assistant",
    "priorities": {
        "cost": "medium",
        "quality": "high",
        "latency": "medium",
        "context_length": "medium"
    },
    "monthly_budget_usd": 100,
    "expected_tokens_per_month": 5000000
}

try:
    response = requests.post(
        "http://localhost:5000/api/v2/analyst/recommend/ai",
        json=payload,
        timeout=300
    )
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
