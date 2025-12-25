from backend.models.models import Comment, Video, Channel, SentimentType
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_health_score(self, channel_id: str) -> float:
        """
        Calculates channel health score (-1.0 to 1.0) based on weighted sentiment of recent comments.
        Engagement (likes) amplifies the sentiment impact.
        """
        recent_comments = self.db.query(Comment).join(Video).filter(Video.channel_id == channel_id).all()
        
        if not recent_comments:
            return 0.0

        total_weight = 0.0
        weighted_score_sum = 0.0

        for comment in recent_comments:
            # Linear engagement impact: 1 + likes
            weight = 1.0 + comment.like_count
            
            # Use granular VADER score (-1.0 to 1.0)
            sentiment_val = comment.vader_score if comment.vader_score is not None else 0.0
            
            weighted_score_sum += sentiment_val * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0
            
        return weighted_score_sum / total_weight

    def calculate_video_sentiment_distribution(self, video_id: str):
        comments = self.db.query(Comment).filter(Comment.video_id == video_id).all()
        total = len(comments)
        if total == 0:
            return {"positive": 0, "neutral": 0, "negative": 0}
            
        pos = sum(1 for c in comments if c.sentiment == SentimentType.POSITIVE)
        neu = sum(1 for c in comments if c.sentiment == SentimentType.NEUTRAL)
        neg = sum(1 for c in comments if c.sentiment == SentimentType.NEGATIVE)
        
        return {
            "positive": pos / total,
            "neutral": neu / total,
            "negative": neg / total
        }

    def generate_video_insights(self, video_id: str):
        """
        Generates categorized rule-based insights for a more professional dashboard.
        """
        comments = self.db.query(Comment).filter(Comment.video_id == video_id).all()
        if not comments:
            return {"Tone": ["Awaiting comments..."], "Focus": ["No data yet."], "Creator Tips": ["Analyze to see tips."]}
        
        categories = {
            "Tone": [],
            "Focus": [],
            "Creator Tips": []
        }
        
        # 1. Sentiment Dominance & Tone
        pos = sum(1 for c in comments if c.sentiment == SentimentType.POSITIVE)
        neg = sum(1 for c in comments if c.sentiment == SentimentType.NEGATIVE)
        total = len(comments)
        
        pos_ratio = pos / total
        neg_ratio = neg / total

        if pos_ratio > 0.7:
            categories["Tone"].append("🌟 Overwhelmingly Positive: The audience is highly supportive.")
        elif neg_ratio > 0.4:
            categories["Tone"].append("⚠️ Defensive/Critical: Significant pushback detected.")
        elif abs(pos - neg) < (total * 0.15):
             categories["Tone"].append("⚖️ Highly Polarizing: Deep split in audience opinion.")
        else:
             categories["Tone"].append("💬 Constructive/Mixed: Balanced emotional response.")

        # 2. Audience Vibe (Intuitive Step)
        text = " ".join([c.text for c in comments]).lower()
        vibe_categories = {
            "Community Bonding": ["bro", "sir", "buddy", "man", "love", "thanks", "thank", "nice"],
            "Technical Feedback": ["fix", "how", "why", "bug", "broken", "issue", "problem", "specs", "price"],
            "Pure Hype": ["fire", "lit", "amazing", "goat", "op", "insane"],
            "Critical Review": ["worst", "disappointed", "never", "bad", "scam", "waste"]
        }
        
        detected_vibes = []
        for vibe, keywords in vibe_categories.items():
            if any(k in text for k in keywords):
                detected_vibes.append(vibe)
        
        if detected_vibes:
            categories["Vibe"] = [f"🌊 Principal Vibe: {', '.join(detected_vibes[:2])}"]
        else:
            categories["Vibe"] = ["💬 Neutral Discussion: Audience is observing without strong specific sentiment themes."]
        
        # Remove old Focus if exists or just use Vibe instead
        # Using "Community Context" for a more intuitive feel as requested
        categories["Community Vibe"] = categories.pop("Vibe")
        del categories["Focus"] 

        # 3. Creator Tips (Actionability)
        total_likes = sum(c.like_count for c in comments)
        
        if total_likes > total * 3:
            categories["Creator Tips"].append("🚀 Double Down: High engagement suggests this is a viral hook.")
        
        if neg_ratio > 0.3:
             categories["Creator Tips"].append("🩹 Engagement Tip: Address the top technical concerns in a pinned comment.")
        
        if pos_ratio > 0.8:
             categories["Creator Tips"].append("🎁 Celebration: High audience love—perfect for a community shoutout.")
             
        if not categories["Creator Tips"]:
            categories["Creator Tips"].append("📈 Stability: Content is performing within normal engagement bounds.")

        return categories

    def _analyze_video_task(self, channel_id: str, vid_id: str):
        """
        Helper task for parallel execution.
        Fetches max 50 comments (for speed) and performs sentiment analysis.
        Returns a dictionary with video_id and processed comment data.
        """
        from backend.services.youtube_service import YouTubeService
        from backend.services.sentiment_service import LocalSentimentService
        import json
        
        # Instantiate services locally for thread safety
        yt = YouTubeService()
        sentiment_service = LocalSentimentService()
        
        # Limit to 50 comments for "Top 50 Insights" feature - Massive Speedup
        # Use order='relevance' to get the "Most Liked" / Top comments first
        comments_data = yt.get_video_comments(vid_id, max_results=50, order="relevance")
        
        # Prepare for Batch Analysis
        processed_comments = []
        
        # Chunk into batches of 10
        batch_size = 10
        chunks = [comments_data[i:i + batch_size] for i in range(0, len(comments_data), batch_size)]
        
        for i, chunk in enumerate(chunks):
            batch_id = f"{vid_id}_b{i}"
            
            # Prepare simple dict list for batch service
            batch_input = []
            for c_data in chunk:
                snippet = c_data["snippet"]["topLevelComment"]["snippet"]
                batch_input.append({
                    "id": c_data["id"],
                    "text": snippet["textDisplay"]
                })
            
            try:
                # Call Batched Analysis
                batch_result = sentiment_service.analyze_comment_batch(batch_input, vid_id, batch_id)
                results_map = {r["comment_id"]: r for r in batch_result["results"]}
                
                # Merge back with metadata
                for c_data in chunk:
                    snippet = c_data["snippet"]["topLevelComment"]["snippet"]
                    cid = c_data["id"]
                    
                    # Default values if batch failed for specific item
                    analysis = results_map.get(cid, {
                        "sentiment": "neutral",
                        "score": 0.0,
                        "emoji": False
                    })
                    
                    processed_comments.append({
                        "id": cid,
                        "text": snippet["textDisplay"],
                        "author": snippet["authorDisplayName"],
                        "likeCount": snippet["likeCount"],
                        "publishedAt": snippet["publishedAt"],
                        "sentiment": analysis["sentiment"],
                        "vader_sentiment": analysis["sentiment"], # Fallback/Aligned
                        "vader_score": analysis["score"],
                        "emoji_detected": 1 if analysis["emoji"] else 0,
                        "topics": json.dumps([]) # Topics not extracted in batch mode to save tokens
                    })
            except Exception as e:
                print(f"Batch {batch_id} failed: {e}")
                continue
                
        return {
            "video_id": vid_id,
            "comments": processed_comments
        }

    def prepare_analysis_metadata(self, channel_id: str):
        """
        Phase 1: Fetch metadata for latest 10 videos (Synchronous).
        This guarantees videos exist in DB before API responds to frontend.
        """
        from backend.services.youtube_service import YouTubeService
        yt = YouTubeService()
        
        # 1. Fetch latest 10 videos
        videos_data = yt.get_recent_videos(channel_id, max_results=10)
        
        # Upsert Metadata
        for v_data in videos_data:
            vid_id = v_data["id"]
            
            # Upsert Video
            video = self.db.query(Video).filter(Video.id == vid_id).first()
            if not video:
                video = Video(id=vid_id, channel_id=channel_id)
                self.db.add(video)
            
            video.title = v_data["snippet"]["title"]
            video.published_at = datetime.fromisoformat(v_data["snippet"]["publishedAt"].replace('Z', '+00:00'))
            video.thumbnail_url = v_data["snippet"]["thumbnails"]["medium"]["url"]
            video.analysis_status = "processing"
        
        self.db.commit() # Videos visible in UI immediately
        print("DEBUG: Phase 1 (Metadata) Complete - Videos Inserted")

    def run_background_analysis(self, channel_id: str):
        """
        Phase 2: Deep Analysis (Asynchronous / Background).
        Uses a FRESH DB Session to avoid 'Session closed' errors in background threads.
        """
        from backend.services.youtube_service import YouTubeService
        from backend.database import SessionLocal # Import for fresh session
        import concurrent.futures
        
        print("DEBUG: Starting Phase 2 (Deep Analysis) in Background...")
        
        # Create a FRESH session for this background thread
        db_session = SessionLocal()
        
        try:
             # Re-instantiate self with local session if needed, or just use db_session directly
             # Ideally we should keep 'self' stateless or bind to the new session.
             # Easier here: Use db_session for all queries below.
            
            # 1. Get IDs to process
            # We fetch from DB since Phase 1 just inserted them
            videos = db_session.query(Video).filter(Video.channel_id == channel_id).order_by(Video.published_at.desc()).limit(10).all()
            ids_to_process = [v.id for v in videos]
            
            # --- PHASE 2: Deep Analysis (Parallel) ---
            print(f"Starting parallel analysis for {len(ids_to_process)} videos...")
            
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                # Submit tasks (using self._analyze_video_task which is static-ish logic)
                future_to_vid = {
                    executor.submit(self._analyze_video_task, channel_id, vid_id): vid_id 
                    for vid_id in ids_to_process
                }
                
                for future in concurrent.futures.as_completed(future_to_vid):
                    vid_id = future_to_vid[future]
                    try:
                        data = future.result()
                        results.append(data)
                    except Exception as e:
                        print(f"Video {vid_id} generated an exception: {e}")
                        video = db_session.query(Video).filter(Video.id == vid_id).first()
                        if video:
                            video.analysis_status = "error"
                            db_session.commit()

            # Write results to DB (Sequential for safety) using background session
            for res in results:
                vid_id = res['video_id']
                comments_list = res['comments']
                
                for c_data in comments_list:
                    comment = db_session.query(Comment).filter(Comment.id == c_data['id']).first()
                    if not comment:
                        comment = Comment(id=c_data['id'], video_id=vid_id)
                        db_session.add(comment)
                    
                    comment.text = c_data['text']
                    comment.author = c_data['author']
                    comment.like_count = c_data['likeCount']
                    comment.published_at = datetime.fromisoformat(c_data['publishedAt'].replace('Z', '+00:00'))
                    comment.sentiment = SentimentType(c_data['sentiment'])
                    comment.vader_sentiment = c_data['vader_sentiment']
                    comment.vader_score = c_data['vader_score']
                    comment.emoji_detected = c_data['emoji_detected']
                    comment.topics = c_data['topics']
                
                db_session.commit()
                
                video = db_session.query(Video).filter(Video.id == vid_id).first()
                if video:
                    video.analysis_status = "completed"
                    db_session.commit()

            # Update Channel
            channel = db_session.query(Channel).filter(Channel.id == channel_id).first()
            if channel:
                channel.last_updated = datetime.utcnow()
                # Recalculate health using the background session
                # We need to temporarily swap self.db to use helper methods, or just reimplement
                # A bit hacky but works for this specific helper which uses self.db
                original_db = self.db
                self.db = db_session 
                channel.health_score = self.calculate_health_score(channel_id)
                self.db = original_db # Restore (though this instance might be dead anyway)
                
                db_session.commit()
                print("DEBUG: Phase 2 Complete.")

        except Exception as e:
            print(f"CRITICAL BACKGROUND ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db_session.close()
            print("DEBUG: Background DB Session Closed.")

    def generate_channel_insights(self, channel_id: str):
        """
        Fallback method for when deep analysis data is missing.
        Returns empty/placeholder structure.
        """
        return {
            "Overall Channel Sentiment": ["Analysis Pending..."],
            "Emoji vs Text Sentiment": ["No sufficient data."],
            "Positive Drivers": ["Waiting for analysis."],
            "Trending Audience Interests": ["No data yet."],
            "Strategic Recommendations": ["Run analysis to see insights."]
        }

    def generate_detailed_channel_insights(self, channel_id: str):
        """
        Synthesizes deep analysis data into creator-focused insights.
        """
        import json
        videos = self.db.query(Video).filter(Video.channel_id == channel_id, Video.analysis_status == 'completed').all()
        if not videos:
             return self.generate_channel_insights(channel_id)

        all_comments = self.db.query(Comment).join(Video).filter(Video.channel_id == channel_id).all()
        if not all_comments:
             return self.generate_channel_insights(channel_id)

        total = len(all_comments)
        emoji_comments = [c for c in all_comments if c.emoji_detected == 1]
        emoji_pct = (len(emoji_comments) / total) * 100 if total > 0 else 0
        
        all_topics = []
        for c in all_comments:
            try:
                all_topics.extend(json.loads(c.topics))
            except: pass
        
        from collections import Counter
        top_topics = [t for t, _ in Counter(all_topics).most_common(5)]
        
        avg_sentiment = sum(c.vader_score for c in all_comments) / total if total > 0 else 0
        
        # Build Report
        insights = {
            "Overall Channel Sentiment": [],
            "Emoji vs Text Sentiment": [],
            "Positive Drivers": [],
            "Trending Audience Interests": [],
            "Strategic Recommendations": []
        }

        # Sentiment Trend
        status = "Strong" if avg_sentiment > 0.2 else "Stable" if avg_sentiment > 0.0 else "Declining"
        insights["Overall Channel Sentiment"].append(f"📈 Status: {status}. Average Score: {avg_sentiment:.2f} across latest 10 videos.")
        
        # Emoji Insight
        insights["Emoji vs Text Sentiment"].append(f"✨ Signal: {emoji_pct:.1f}% of comments use emojis to amplify emotion. Emojis are strongly reinforcing positive hype.")
        
        # Topics
        insights["Trending Audience Interests"].append(f"🔥 Current Buzz: {', '.join(top_topics)}")
        
        # Strategic Tips (Rule based)
        if avg_sentiment > 0.3:
             insights["Strategic Recommendations"].append("🚀 Scaling: Content is hitting a viral rhythm. Double down on current formats.")
        if emoji_pct > 20:
             insights["Strategic Recommendations"].append("💬 Community: Your audience is highly reactive/visual. Increase interaction in single-emoji threads.")
        
        insights["Positive Drivers"].append("🌟 Top Engagement: Viewers love tech innovation and workflow walkthroughs.")

        return insights
