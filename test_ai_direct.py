
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_ai_integration():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY not found in .env")
        return

    # Sample knowledge base snippet
    sample_info = """
    # Dynamic Contact Resistance Measurement (DCRM)
    Healthy conduction resistance is typically 20-80 micro-ohms.
    Arc duration interpretation: 5-15 ms is Normal, 15-30 ms is Moderate wear, > 40 ms is Severe fault.
    """

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": f"You are a Field Advisor. Use this info: {sample_info}"},
            {"role": "user", "content": "What is the healthy range for conduction resistance?"}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        res_json = response.json()
        answer = res_json['choices'][0]['message']['content']
        print(f"✅ AI Response: {answer}")
        
        if "20" in answer and "80" in answer:
            print("✅ Grounding verified: Answer contains expected values (20-80).")
        else:
            print("❌ Grounding failed: Answer does not contain expected values.")
            
    except Exception as e:
        print(f"❌ API Call Failed: {e}")

if __name__ == "__main__":
    test_ai_integration()
