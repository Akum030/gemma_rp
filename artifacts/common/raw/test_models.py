import requests
import json

API_KEY = "os.environ.get("API_KEY", "")"
API_URL = "https://imllm.intermesh.net/v1/chat/completions"

models_to_test = [
    "google/gemini-3-pro-preview",
    "qwen/qwen3-32b", 
    "anthropic/claude-sonnet-4",
    "google/gemini-2.0-flash"  # Original working model
]

test_prompt = "Extract attributes from: hdpe extruder 240v"

print("Testing model accessibility...\n")

for model in models_to_test:
    print(f"Testing: {model}")
    try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": test_prompt}],
            "temperature": 0,
            "max_tokens": 100
        }
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            print(f"  ✓ SUCCESS - Model is accessible")
            data = response.json()
            print(f"  Response: {data['choices'][0]['message']['content'][:100]}...")
        else:
            print(f"  ✗ FAILED - HTTP {response.status_code}")
            print(f"  Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"  ✗ EXCEPTION: {str(e)}")
    
    print()
