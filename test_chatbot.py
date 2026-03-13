import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_chatbot():
    url = "http://localhost:5000/api/chatbot/ask"
    
    # We need to simulate a logged-in user or bypass login for this test if possible.
    # However, since the app is running with Flask-Login, it might be easier to test
    # the Groq API integration directly first to ensure the key and logic work.
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY not found in .env")
        return

    print(f"Testing Groq API with key: {api_key[:10]}...")
    
    # Load knowledge base
    info_content = ""
    try:
        with open('data/dcrm_info_clean.md', 'rb') as f:
            data = f.read()
            print(f"DEBUG: File size {len(data)} bytes")
            print(f"DEBUG: First 100 bytes (hex): {data[:100].hex()}")
            info_content = data.decode('utf-8', errors='replace')
    except Exception as e:
        import traceback
        print(f"❌ Could not load dcrm_info.md: {e}")
        traceback.print_exc()
        return

    system_prompt = (
        "You are the 'Field Advisor', an expert assistant for the DCRM system. "
        "Use the provided technical reference documentation to answer questions accurately.\n\n"
        f"TECHNICAL DOCUMENTATION:\n{info_content}"
    )
    
    question = "What is the healthy range for conduction resistance?"
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                "temperature": 0.2,
                "max_tokens": 1024
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            print(f"✅ Chatbot Response: {answer}")
            
            # Check if answer contains info from the doc (20-80 µΩ)
            if "20" in answer and "80" in answer:
                print("✅ Grounding verified: Response contains information from dcrm_info.md")
            else:
                print("⚠ Grounding warning: Response might not be using dcrm_info.md correctly.")
        else:
            print(f"❌ Groq API Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Test Error: {e}")

if __name__ == "__main__":
    test_chatbot()
