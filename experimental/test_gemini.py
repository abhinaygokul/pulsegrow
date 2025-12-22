import google.generativeai as genai
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('/Users/abhi/Dev/pulsegrow/experimental/backend/.env')
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("GOOGLE_API_KEY not found")
else:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Hello")
        print(f"SUCCESS: {response.text}")
    except Exception as e:
        print(f"FAILURE: {e}")
