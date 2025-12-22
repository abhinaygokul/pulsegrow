import json
import os
import re
from backend.services.sentiment_service import LocalSentimentService

# Simulated Gemini Instructions Implementation
def simulate_gemini_analysis(video_id, video_title, batch_id, comments):
    sentiment_service = LocalSentimentService()
    results = []
    
    for c in comments:
        text = c.get('text', '')
        cid = c.get('comment_id', '')
        
        # Emoji detection logic
        emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)
        emoji_detected = bool(emoji_pattern.search(text))
        
        # Reuse existing service which is already somewhat emoji-aware
        analysis = sentiment_service.analyze_comment(text)
        
        vader = analysis.get('vader', {})
        label = vader.get('sentiment', 'neutral')
        score = vader.get('score', 0.0)
        
        # Extract 1-3 topics (simplified)
        words = re.findall(r'\b\w{4,}\b', text.lower())
        topics = list(set([w for w in words if w not in ['this', 'that', 'with', 'from', 'have', 'your', 'about', 'really']]))[:3]
        
        results.append({
            "comment_id": cid,
            "sentiment_label": label,
            "sentiment_score": score,
            "topics": topics,
            "emoji_detected": emoji_detected
        })
        
    return {
        "video_id": video_id,
        "video_title": video_title,
        "batch_id": batch_id,
        "results": results
    }

def orchestrate():
    if not os.path.exists('mkbhd_analysis_input.json'):
        print("Input file missing.")
        return
        
    with open('mkbhd_analysis_input.json', 'r') as f:
        data = json.load(f)
        
    all_batch_results = []
    
    for video in data:
        video_id = video['video_id']
        video_title = video['video_title']
        comments = video['comments']
        
        # Batch comments into sets of 200
        for i in range(0, len(comments), 200):
            batch = comments[i:i+200]
            batch_id = f"{video_id}_batch_{i//200}"
            print(f"Processing batch {batch_id} for {video_title}...")
            
            # Delegate to (simulated) Gemini
            batch_output = simulate_gemini_analysis(video_id, video_title, batch_id, batch)
            all_batch_results.append(batch_output)
            
    with open('mkbhd_batch_results.json', 'w') as f:
        json.dump(all_batch_results, f, indent=2)
        
    print(f"Orchestration complete. Processed {len(all_batch_results)} batches.")

if __name__ == "__main__":
    orchestrate()
