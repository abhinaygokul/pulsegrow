import json
from collections import Counter

def aggregate():
    with open('mkbhd_batch_results.json', 'r') as f:
        batches = json.load(f)
        
    video_data = {}
    
    for b in batches:
        vid_id = b['video_id']
        vid_title = b['video_title']
        
        if vid_id not in video_data:
            video_data[vid_id] = {
                "title": vid_title,
                "total_comments": 0,
                "sentiment_sum": 0,
                "sentiment_counts": {"positive": 0, "neutral": 0, "negative": 0},
                "emoji_sentiment_count": 0,
                "topics": []
            }
            
        res = b['results']
        video_data[vid_id]["total_comments"] += len(res)
        
        for r in res:
            video_data[vid_id]["sentiment_sum"] += r['sentiment_score']
            video_data[vid_id]["sentiment_counts"][r['sentiment_label']] += 1
            if r['emoji_detected']:
                video_data[vid_id]["emoji_sentiment_count"] += 1
            video_data[vid_id]["topics"].extend(r['topics'])
            
    # Finalize per-video stats
    summary = []
    all_video_scores = []
    
    for vid_id, data in video_data.items():
        avg_score = data["sentiment_sum"] / data["total_comments"] if data["total_comments"] > 0 else 0
        all_video_scores.append(avg_score)
        
        topic_counts = Counter(data["topics"])
        top_topics = [t for t, _ in topic_counts.most_common(5)]
        
        emoji_pct = (data["emoji_sentiment_count"] / data["total_comments"]) * 100 if data["total_comments"] > 0 else 0
        
        summary.append({
            "video_id": vid_id,
            "title": data["title"],
            "avg_sentiment": avg_score,
            "sentiment_distribution": data["sentiment_counts"],
            "emoji_driven_pct": emoji_pct,
            "top_topics": top_topics
        })
        
    # Channel trends
    channel_avg = sum(all_video_scores) / len(all_video_scores) if all_video_scores else 0
    
    # Sort summary by date? (assuming order of videos was latest first)
    # We'll just provide the summary as is.
    
    output = {
        "channel_summary": {
            "overall_avg_sentiment": channel_avg,
            "video_count": len(summary)
        },
        "videos": summary
    }
    
    with open('mkbhd_aggregation_results.json', 'w') as f:
        json.dump(output, f, indent=2)
        
    print("Aggregation complete.")

if __name__ == "__main__":
    aggregate()
