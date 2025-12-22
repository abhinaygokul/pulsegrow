import google.generativeai as genai
import os
import time
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('/Users/abhi/Dev/pulsegrow/experimental/backend/.env')
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY not found in .env")
else:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Ping")
        print(f"SUCCESS: {response.text}")
        
        print("Testing rate limit (Free Tier typical is 15 RPM/1M TPM)...")
        start_time = time.time()
        for i in range(3):
            model.generate_content(f"Test {i}")
            print(f"Request {i+1} OK")
        
        print("\nGemini 2.0 Flash is ACTIVE and WORKING.")
        print("Key Tier: likely Free (requires Pay-as-you-go for higher limits).")
        print("Limits: Standard Free tier for 2.0 Flash is generally 15 RPM.")
        
    except Exception as e:
        print(f"FAILURE: {e}")
