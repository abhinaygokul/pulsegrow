import os
import json
import datetime
from backend.services.youtube_service import YouTubeService

def fetch_data():
    yt = YouTubeService()
    channel_id = 'UCBJycsmduvYEL83R_U4JriQ' # MKBHD
    print(f"Fetching latest 10 videos for channel: {channel_id}")
    
    videos = yt.get_recent_videos(channel_id, max_results=10)
    data = []
    
    for v in videos:
        vid_id = v['id']
        vid_title = v['snippet']['title']
        print(f"Fetching comments for video: {vid_title} ({vid_id})")
        
        # Fetching comments - set a reasonable limit for this orchestration
        # "All comments" could be 50k+, we'll try to get ALL now to verify the fix
        comments_data = yt.get_video_comments(vid_id, max_results=None)
        
        video_comments = []
        for c in comments_data:
            snippet = c['snippet']['topLevelComment']['snippet']
            video_comments.append({
                "comment_id": c['id'],
                "text": snippet['textDisplay'],
                "author": snippet['authorDisplayName'],
                "published_at": snippet['publishedAt']
            })
            
        data.append({
            "video_id": vid_id,
            "video_title": vid_title,
            "comments": video_comments
        })
        
    with open('mkbhd_analysis_input.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Successfully fetched data for {len(data)} videos.")

if __name__ == "__main__":
    fetch_data()
