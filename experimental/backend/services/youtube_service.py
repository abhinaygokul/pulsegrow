from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

from pathlib import Path

# Explicitly load from backend/.env or parent .env
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / '.env'

load_dotenv(dotenv_path=env_path)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

class YouTubeService:
    def __init__(self):
        if not YOUTUBE_API_KEY:
            print("Warning: YOUTUBE_API_KEY not found in environment variables.")
            self.youtube = None
        else:
            self.youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    def get_channel_details(self, channel_id: str):
        if not self.youtube or channel_id == "demo":
             return {
                "snippet": {
                    "title": "PulseGrow Demo Channel",
                    "thumbnails": {"default": {"url": "https://api.dicebear.com/7.x/avataaars/svg?seed=PulseGrow"}},
                },
                "contentDetails": {
                    "relatedPlaylists": {
                        "uploads": "demo_uploads_playlist" # dummy
                    }
                }
            }
        
        # Handle URL input
        if "youtube.com" in channel_id or "youtu.be" in channel_id:
             # Try to extract handle or ID
             if "@" in channel_id:
                 channel_id = "@" + channel_id.split("@")[-1].split("/")[0]
             elif "/channel/" in channel_id:
                 channel_id = channel_id.split("/channel/")[-1].split("/")[0]

        # Handle Handle input (e.g. @mkbhd)
        if channel_id.startswith("@"):
            request = self.youtube.channels().list(
                part="snippet,statistics,contentDetails",
                forHandle=channel_id
            )
        else:
            # Assume Channel ID
            request = self.youtube.channels().list(
                part="snippet,statistics,contentDetails",
                id=channel_id
            )
            
        response = request.execute()
        if "items" in response and len(response["items"]) > 0:
            return response["items"][0]
        return None

    def get_recent_videos(self, channel_id: str, max_results: int = 10):
        if not self.youtube or channel_id == "demo":
            return [
                {
                    "id": "Ks-_Mh1QhMc",
                    "contentDetails": {"videoId": "Ks-_Mh1QhMc"},
                    "snippet": {
                        "title": "Your Body Language May Shape Who You Are | Amy Cuddy",
                        "publishedAt": "2012-10-01T10:00:00Z",
                        "thumbnails": {
                            "medium": {"url": "https://i.ytimg.com/vi/Ks-_Mh1QhMc/mqdefault.jpg"},
                            "default": {"url": "https://i.ytimg.com/vi/Ks-_Mh1QhMc/default.jpg"}
                        }
                    }
                },
                {
                   "id": "ufJTTcuXVUU",
                   "contentDetails": {"videoId": "ufJTTcuXVUU"},
                    "snippet": {
                        "title": "The power of vulnerability | Brené Brown",
                        "publishedAt": "2011-01-01T14:30:00Z",
                        "thumbnails": {
                            "medium": {"url": "https://i.ytimg.com/vi/ufJTTcuXVUU/mqdefault.jpg"},
                            "default": {"url": "https://i.ytimg.com/vi/ufJTTcuXVUU/default.jpg"}
                        }
                    } 
                },
                {
                   "id": "rrkrvAUbU9Y",
                   "contentDetails": {"videoId": "rrkrvAUbU9Y"},
                    "snippet": {
                        "title": "The puzzle of motivation | Dan Pink",
                        "publishedAt": "2009-08-25T09:15:00Z",
                        "thumbnails": {
                            "medium": {"url": "https://i.ytimg.com/vi/rrkrvAUbU9Y/mqdefault.jpg"},
                            "default": {"url": "https://i.ytimg.com/vi/rrkrvAUbU9Y/default.jpg"}
                        }
                    } 
                }
            ]

        # First get uploads playlist ID
        channel_data = self.get_channel_details(channel_id)
        if not channel_data:
            return []
        
        uploads_playlist_id = channel_data["contentDetails"]["relatedPlaylists"]["uploads"]
        
        request = self.youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=max_results
        )
        response = request.execute()
        playlist_items = response.get("items", [])
        
        if not playlist_items:
            return []
            
        # Extract video IDs to fetch statistics
        video_ids = [item["contentDetails"]["videoId"] for item in playlist_items]
        
        # Fetch statistics for these videos
        stats_request = self.youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(video_ids)
        )
        stats_response = stats_request.execute()
        return stats_response.get("items", [])

    def get_video_comments(self, video_id: str, max_results: int = 100):
        if not self.youtube or video_id.startswith("demo_"):
             return [
                {"id": "c1", "snippet": {"topLevelComment": {"snippet": {"textDisplay": "This is exactly what I needed! Finally proper analytics.", "authorDisplayName": "CreatorFan1", "likeCount": 120, "publishedAt": "2023-10-25T10:05:00Z"}}}},
                {"id": "c2", "snippet": {"topLevelComment": {"snippet": {"textDisplay": "Not sure about the UI, looks a bit cluttered.", "authorDisplayName": "Critic007", "likeCount": 5, "publishedAt": "2023-10-25T11:20:00Z"}}}},
                {"id": "c3", "snippet": {"topLevelComment": {"snippet": {"textDisplay": "Can you add support for Instagram soon?", "authorDisplayName": "InstaStar", "likeCount": 45, "publishedAt": "2023-10-25T12:00:00Z"}}}},
                {"id": "c4", "snippet": {"topLevelComment": {"snippet": {"textDisplay": "Super helpful tool.", "authorDisplayName": "GrowthHacker", "likeCount": 12, "publishedAt": "2023-10-25T13:45:00Z"}}}},
                 {"id": "c5", "snippet": {"topLevelComment": {"snippet": {"textDisplay": "Pricing is too high for small creators.", "authorDisplayName": "SmallTimer", "likeCount": 8, "publishedAt": "2023-10-25T14:10:00Z"}}}}
            ]

        try:
            all_comments = []
            next_page_token = None
            
            # Use configurable limit or default to None (Unlimited)
            env_max = os.getenv("MAX_COMMENTS_PER_VIDEO")
            
            # Determine effective limit
            # Priority: 1. Function Argument (if set), 2. Env Var, 3. Unlimited
            effective_limit = max_results
            if effective_limit is None and env_max:
                try:
                    effective_limit = int(env_max)
                except ValueError:
                    pass
            
            while True:
                # Check limit
                if effective_limit and len(all_comments) >= effective_limit:
                    break

                # Calculate fetch size for this batch
                fetch_size = 100
                if effective_limit:
                    remaining = effective_limit - len(all_comments)
                    fetch_size = min(100, remaining)
                
                if fetch_size <= 0:
                    break

                request = self.youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=fetch_size,
                    textFormat="plainText",
                    pageToken=next_page_token
                )
                response = request.execute()
                items = response.get("items", [])
                all_comments.extend(items)
                
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
                    
            return all_comments
        except Exception as e:
            print(f"Error fetching comments for video {video_id}: {e}")
            return []
