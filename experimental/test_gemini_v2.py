import google.generativeai as genai
import os
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
        model = genai.GenerativeModel('gemini-1.5-flash') # Using 1.5 flash as a safe default
        response = model.generate_content("Ping")
        print(f"SUCCESS: {response.text}")
        
        # Checking for common limit info in headers if possible via SDK usually isn't direct, 
        # but we can try a small burst to see if we hit 429
        print("Testing rate limit (burst of 5)...")
        for i in range(5):
            model.generate_content(f"Echo {i}")
        print("Burst successful. Key seems active with standard tier.")
        
    except Exception as e:
        print(f"FAILURE: {e}")
