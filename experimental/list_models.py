import google.generativeai as genai
import os

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # Try to read from .env manually if not in env
    try:
        with open('.env') as f:
            for line in f:
                if line.startswith('GEMINI_API_KEY='):
                    api_key = line.strip().split('=')[1]
                    break
    except:
        pass

if not api_key:
    print("No API Key found")
else:
    genai.configure(api_key=api_key)
    print("Listing models...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Error: {e}")
