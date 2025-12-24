import json
import os
from backend.services.sentiment_service import LocalSentimentService
import google.generativeai as genai

# Mock DB Object behavior since service expects dicts/objects
class MockComment:
    def __init__(self, c_data):
        self.text = c_data.get("text", "")
        self.author = c_data.get("author", "User")
        self.like_count = 0 # Default since JSON might not have it, but for MKBHD logic we need it
        # Actually the provided json example doesn't show likes in the array, let's fake it for test or check if it has it
        # The input file mkbhd_analysis_input.json DOES NOT contain like counts in the provided snippet.
        # But real API responses DO. I will simulate random likes for verification.
        import random
        self.like_count = random.randint(0, 5000)

def verify():
    print("--- Verifying Top 50 Insights Logic ---")
    
    # Init Service
    service = LocalSentimentService()
    
    # Load Data
    with open('mkbhd_analysis_input.json', 'r') as f:
        data = json.load(f)
        
    video_1 = data[0]
    print(f"Analyzing Video: {video_1['video_title']}")
    
    comments_list = []
    for c in video_1['comments']:
         comments_list.append({
             "text": c.get("text"),
             "author": c.get("author"),
             "like_count": 0 
         })
         
    # Mock some likes for sorting test
    import random
    for i, c in enumerate(comments_list):
        c["like_count"] = random.randint(1, 1000)
    
    # Force one to be super high
    comments_list[0]["like_count"] = 99999
    comments_list[0]["text"] = "This is the best video ever created in history!"
    
    print(f"Total Comments: {len(comments_list)}")
    
    # Call Method
    insights = service.generate_top_50_insights(comments_list)
    
    print("\n--- INSIGHTS RESULT ---")
    print(json.dumps(insights, indent=2))
    
    if "sentiment_summary" in insights:
        print("\nSUCCESS: Insights Generated.")
    else:
        print("\nFAILURE: Keys missing.")

if __name__ == "__main__":
    verify()
