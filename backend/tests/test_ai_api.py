import requests
import json

url = "http://localhost:5000/api/v2/analyst/recommend/ai"
payload = {
    "use_case": "chatbot for company customer support",
    "priorities": {
        "cost": "low",
        "quality": "high",
        "latency": "medium",
        "context_length": "medium"
    },
    "monthly_budget_usd": 100,
    "expected_tokens_per_month": 5000000
}

try:
    response = requests.post(url, json=payload, timeout=60)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
