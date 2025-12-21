from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.youtube_service import YouTubeService
from backend.services.sentiment_service import LocalSentimentService
from backend.services.analytics_service import AnalyticsService
from backend.models.models import Channel, Video, Comment, SentimentType
import datetime

router = APIRouter()
youtube_service = YouTubeService()
sentiment_service = LocalSentimentService()

import traceback

@router.post("/channel/{channel_id}/analyze")
def analyze_channel(channel_id: str, db: Session = Depends(get_db)):
    print(f"DEBUG: HIT analyze_channel with ID: {channel_id}")
    try:
        # 1. Fetch Channel Info
        channel_data = youtube_service.get_channel_details(channel_id)
        if not channel_data:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        # Update/Create Channel
        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            channel = Channel(id=channel_id)
            db.add(channel)

    
        channel.title = channel_data["snippet"]["title"]
        channel.thumbnail_url = channel_data["snippet"]["thumbnails"]["default"]["url"]
        
        # 2. Fetch Recent Videos
        videos_data = youtube_service.get_recent_videos(channel_id)
        
        # 3. Fetch & Store Recent Videos (Metadata Only)
        # We do NOT analyze comments here. That happens on-demand when user clicks a video.
        for v_data in videos_data:
            vid_id = v_data["id"] 
            video = db.query(Video).filter(Video.id == vid_id).first()
            if not video:
                video = Video(id=vid_id, channel_id=channel_id)
                db.add(video)
            
            video.title = v_data["snippet"]["title"]
            video.published_at = datetime.datetime.fromisoformat(v_data["snippet"]["publishedAt"].replace('Z', '+00:00'))
            video.thumbnail_url = v_data["snippet"]["thumbnails"]["medium"]["url"] if "medium" in v_data["snippet"]["thumbnails"] else ""
            
            # Update statistics if available
            if "statistics" in v_data:
                stats = v_data["statistics"]
                video.view_count = int(stats.get("viewCount", 0)) 
                video.like_count = int(stats.get("likeCount", 0))
                video.comment_count = int(stats.get("commentCount", 0))
            
            # NOTE: We skip get_video_comments() and sentiment analysis here.
            # This makes the channel load "instant".

            db.commit()
        # 4. Calculate Health Score
        analytics = AnalyticsService(db)
        channel.health_score = analytics.calculate_health_score(channel_id)
        db.commit()
        
        return {"status": "analyzed", "channel_title": channel.title, "health_score": channel.health_score}

    except Exception as e:
        print(f"CRITICAL ERROR in analyze_channel: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

@router.get("/channel/{channel_id}")
def get_channel(channel_id: str, db: Session = Depends(get_db)):
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel

@router.get("/channel/{channel_id}/videos")
def get_channel_videos(channel_id: str, db: Session = Depends(get_db)):
    videos = db.query(Video).filter(Video.channel_id == channel_id).all()
    return videos

@router.get("/video/{video_id}")
def get_video_details(video_id: str, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
        
    analytics = AnalyticsService(db)
    distribution = analytics.calculate_video_sentiment_distribution(video_id)
    insights = analytics.generate_video_insights(video_id)
    
    insights = analytics.generate_video_insights(video_id)
    
    # Get Comparison Data (Shared Logic)
    comparison_data = _get_comparison_data(db, video_id)

    # Calculate analyzed count locally
    analyzed_count = db.query(Comment).filter(Comment.video_id == video_id).count()

    return {
        "video": video,
        "sentiment_distribution": distribution,
        "comparison": comparison_data,
        "insights": insights,
        "analyzed_comment_count": analyzed_count
    }

def _get_comparison_data(db: Session, video_id: str):
    """Helper to calculate VADER vs Gemini stats from stored comments."""
    comments = db.query(Comment).filter(Comment.video_id == video_id).all()
    if not comments:
        return None

    # VADER
    v_pos = sum(1 for c in comments if c.vader_sentiment == "positive")
    v_neu = sum(1 for c in comments if c.vader_sentiment == "neutral")
    v_neg = sum(1 for c in comments if c.vader_sentiment == "negative")
    v_total = len(comments) or 1
    dist_vader = {"positive": v_pos/v_total, "neutral": v_neu/v_total, "negative": v_neg/v_total}
    
    vader_scores = [c.vader_score for c in comments if c.vader_score is not None]
    vader_avg = sum(vader_scores) / len(vader_scores) if vader_scores else 0.0

    # Gemini
    g_pos = sum(1 for c in comments if c.gemini_sentiment == "positive")
    g_neu = sum(1 for c in comments if c.gemini_sentiment == "neutral")
    g_neg = sum(1 for c in comments if c.gemini_sentiment == "negative")
    g_total = len(comments) or 1
    dist_gemini = {"positive": g_pos/g_total, "neutral": g_neu/g_total, "negative": g_neg/g_total}
    
    gemini_scores = [c.gemini_score for c in comments if c.gemini_score is not None]
    gemini_avg = sum(gemini_scores) / len(gemini_scores) if gemini_scores else 0.0
    
    return {
        "vader": { "distribution": dist_vader, "score": vader_avg },
        "gemini": { "distribution": dist_gemini, "score": gemini_avg }
    }

from fastapi import BackgroundTasks

def process_video_background(video_id: str, db: Session):
    """Background task to fetch ALL comments and analyze them."""
    print(f"BACKGROUND: Starting deep analysis for {video_id}")
    
    try:
        # Update status to processing
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.analysis_status = "processing"
            db.commit()
            
        # Fetch ALL comments (limit 500 for safety)
        comments_data = youtube_service.get_video_comments(video_id, max_results=500)
        
        count_processed = 0
        for c_data in comments_data:
            try:
                snippet = c_data["snippet"]["topLevelComment"]["snippet"]
                cid = c_data["id"]
                
                # Upsert Comment
                # We use a new session or be careful with the existing one passed in? 
                # Better to use a fresh session in real app, but here we reuse for simplicity 
                # (Note: passing session to background task is risky if session closes. 
                # Ideally we create a new session inside this task. For this demo, we'll try reusing or relying on scope.)
                
                # RE-QUERYING to be safe
                comment = db.query(Comment).filter(Comment.id == cid).first()
                if not comment:
                    comment = Comment(id=cid, video_id=video_id)
                    db.add(comment)
                
                comment.text = snippet["textDisplay"]
                comment.author = snippet["authorDisplayName"]
                comment.like_count = snippet["likeCount"]
                comment.published_at = datetime.datetime.fromisoformat(snippet["publishedAt"].replace('Z', '+00:00'))
                
                # Analyze
                analysis = sentiment_service.analyze_comment(comment.text)
                
                if "vader" in analysis:
                    comment.vader_sentiment = analysis["vader"]["sentiment"]
                    comment.vader_score = analysis["vader"]["score"]
                
                if "gemini" in analysis and analysis["gemini"]["available"]:
                    comment.gemini_sentiment = analysis["gemini"]["sentiment"]
                    comment.gemini_score = analysis["gemini"]["score"]
                
                final_s = analysis["final_sentiment"]
                if final_s == "positive": comment.sentiment = SentimentType.POSITIVE
                elif final_s == "negative": comment.sentiment = SentimentType.NEGATIVE
                else: comment.sentiment = SentimentType.NEUTRAL
                
                count_processed += 1
                
                if count_processed % 10 == 0:
                     db.commit() # Commit periodically
                     
            except Exception as e:
                print(f"ERROR processing comment {cid}: {e}")
                continue
        
        db.commit()
        
        # Recalculate Stats
        total_score = 0.0
        total_weight = 0.0
        fresh_comments = db.query(Comment).filter(Comment.video_id == video_id).all()
        for comment in fresh_comments:
            sentiment_val = 0.0
            if comment.sentiment == SentimentType.POSITIVE: sentiment_val = 1.0
            elif comment.sentiment == SentimentType.NEGATIVE: sentiment_val = -1.0
            
            weight = 1.0 + comment.like_count
            total_score += sentiment_val * weight
            total_weight += weight
            
        video = db.query(Video).filter(Video.id == video_id).first()
        if video and total_weight > 0:
            video.sentiment_score = total_score / total_weight
            video.analysis_status = "completed"
            
        # Update Channel Health
        analytics = AnalyticsService(db)
        if video:
            channel_id = video.channel_id
            new_health_score = analytics.calculate_health_score(channel_id)
            channel = db.query(Channel).filter(Channel.id == channel_id).first()
            if channel:
                channel.health_score = new_health_score
        
        db.commit()
        print(f"BACKGROUND: Finished analysis for {video_id}. Processed {count_processed} comments.")
        
    except Exception as e:
        print(f"BACKGROUND ERROR: {e}")
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.analysis_status = "error"
            db.commit()


@router.post("/video/{video_id}/analyze")
def analyze_video(video_id: str, background_tasks: BackgroundTasks, analyze_all: bool = False, db: Session = Depends(get_db)):
    """
    On-Demand Analysis.
    If analyze_all=True, runs in background to fetch ALL comments.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found locally.")

    try:
        if analyze_all:
            # Trigger Background Task
            # Check if column exists dynamically or assume it does? 
            # If we get an error here, it's the schema.
            video.analysis_status = "pending"
            db.commit()
            background_tasks.add_task(process_video_background, video_id, db)
            return {"status": "queued", "message": "Deep analysis started in background."}
        
        # Standard Quick Analysis (Top 10)
        print(f"DEBUG: Quick analysis for video {video_id}...")
        try:
            comments_data = youtube_service.get_video_comments(video_id, max_results=10)
        except Exception as e:
            print(f"ERROR: Failed to fetch value comments: {e}")
            comments_data = [] 
        
        # Process synchronously
        count_processed = 0
        for c_data in comments_data:
            try:
                snippet = c_data["snippet"]["topLevelComment"]["snippet"]
                cid = c_data["id"]
                comment = db.query(Comment).filter(Comment.id == cid).first()
                if not comment:
                    comment = Comment(id=cid, video_id=video_id)
                    db.add(comment)
                comment.text = snippet["textDisplay"]
                comment.author = snippet["authorDisplayName"]
                comment.like_count = snippet["likeCount"]
                comment.published_at = datetime.datetime.fromisoformat(snippet["publishedAt"].replace('Z', '+00:00'))
                analysis = sentiment_service.analyze_comment(comment.text)
                
                if "vader" in analysis:
                    comment.vader_sentiment = analysis["vader"]["sentiment"]
                    comment.vader_score = analysis["vader"]["score"]
                if "gemini" in analysis and analysis["gemini"]["available"]:
                    comment.gemini_sentiment = analysis["gemini"]["sentiment"]
                    comment.gemini_score = analysis["gemini"]["score"]
                    
                final_s = analysis["final_sentiment"]
                if final_s == "positive": comment.sentiment = SentimentType.POSITIVE
                elif final_s == "negative": comment.sentiment = SentimentType.NEGATIVE
                else: comment.sentiment = SentimentType.NEUTRAL
                
                count_processed += 1
            except: continue
            
        db.commit()
        
        video.analysis_status = "completed"
        db.commit()

        # Return standard response
        analytics = AnalyticsService(db)
        dist_main = analytics.calculate_video_sentiment_distribution(video_id)
        comparison_data = _get_comparison_data(db, video_id)
        insights = analytics.generate_video_insights(video_id)
        analyzed_count = db.query(Comment).filter(Comment.video_id == video_id).count()

        return {
            "status": "analyzed",
            "video": video,
            "sentiment_distribution": dist_main,
            "comparison": comparison_data,
            "insights": insights,
            "analyzed_comment_count": analyzed_count
        }

    except Exception as e:
        error_msg = f"CRITICAL ERROR in analyze_video: {e}\n{traceback.format_exc()}"
        print(error_msg)
        with open("backend_errors.txt", "a") as f:
            f.write(f"\n--- {datetime.datetime.now()} ---\n")
            f.write(error_msg)
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

# --- NEW FUNCTIONS FOR SIDEBAR ---

@router.get("/channels")
def get_all_channels(db: Session = Depends(get_db)):
    """Fetch all analyzed channels for the Reports page."""
    channels = db.query(Channel).all()
    return channels

@router.get("/admin/stats")
def get_system_stats(db: Session = Depends(get_db)):
    """Fetch system-wide statistics for the Admin page."""
    total_channels = db.query(Channel).count()
    total_videos = db.query(Video).count()
    total_comments = db.query(Comment).count()
    
    # Calculate average sentiment across all videos
    avg_sentiment = 0.0
    videos = db.query(Video).all()
    if videos:
        avg_sentiment = sum(v.sentiment_score for v in videos) / len(videos)

    return {
        "total_channels": total_channels,
        "total_videos": total_videos,
        "total_comments": total_comments,
        "global_sentiment_average": avg_sentiment
    }

@router.delete("/admin/reset")
def reset_database(db: Session = Depends(get_db)):
    """Clear basic data (Optional Admin Action)."""
    # For safety, we might not want to delete everything in a real app,
    # but for this local tool, it's useful.
    try:
        db.query(Comment).delete()
        db.query(Video).delete()
        db.query(Channel).delete()
        db.commit()
        return {"status": "success", "message": "Database cleared."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
