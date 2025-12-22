from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
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
def analyze_channel(channel_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
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
        db.commit()

        # Trigger Deep Analysis in Background (Workflow Orchestration)
        analytics = AnalyticsService(db)
        background_tasks.add_task(analytics.process_channel_deep_analysis, channel_id)
        
        return {
            "status": "analyzed", 
            "id": channel_id,
            "channel_id": channel_id,
            "channel_title": channel.title, 
            "health_score": channel.health_score, 
            "message": "Deep analysis started in background."
        }

    except Exception as e:
        print(f"CRITICAL ERROR in analyze_channel: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

@router.get("/channel/{channel_id}/insights")
def get_channel_insights(channel_id: str, db: Session = Depends(get_db)):
    """Fetch high-level aggregated insights for a channel."""
    analytics = AnalyticsService(db)
    insights = analytics.generate_detailed_channel_insights(channel_id)
    return insights

@router.get("/channel/{channel_id}")
def get_channel(channel_id: str, db: Session = Depends(get_db)):
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel

@router.get("/channel/{channel_id}/videos")
def get_channel_videos(channel_id: str, db: Session = Depends(get_db)):
    videos = db.query(Video).filter(Video.channel_id == channel_id).all()
    analytics = AnalyticsService(db)
    
    results = []
    for v in videos:
        v_dict = {
            "id": v.id,
            "title": v.title,
            "thumbnail_url": v.thumbnail_url,
            "published_at": v.published_at.isoformat() if v.published_at else None,
            "view_count": v.view_count,
            "like_count": v.like_count,
            "comment_count": v.comment_count,
            "sentiment_score": v.sentiment_score,
            "analysis_status": v.analysis_status,
        }
        
        if v.analysis_status == "completed":
            v_dict["distribution"] = analytics.calculate_video_sentiment_distribution(v.id)
            v_dict["insights"] = analytics.generate_video_insights(v.id)
            
        results.append(v_dict)
        
    return results

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

from fastapi.responses import StreamingResponse
import json

@router.post("/video/{video_id}/analyze")
def analyze_video(video_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):

    """
    On-Demand Analysis with SSE for real-time progress updates.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found locally.")

    def analysis_stream():
        import time
        # Standard constraints
        MAX_GEMINI_CALLS = 10
        COMMENTS_PER_BATCH = 5
        THROTTLE_DELAY = 4.5

        try:
            # 1. Fetch comments
            comments_data = youtube_service.get_video_comments(video_id, max_results=MAX_GEMINI_CALLS * COMMENTS_PER_BATCH)
            if not comments_data:
                yield f"data: {json.dumps({'status': 'completed', 'message': 'No comments found'})}\n\n"
                return

            # Yield Initial State
            total_comments = len(comments_data)
            yield f"data: {json.dumps({'status': 'processing', 'progress': 0, 'total': total_comments})}\n\n"

            processed_count = 0
            
            # 2. Process Batches
            for i in range(0, total_comments, COMMENTS_PER_BATCH):
                batch_data = comments_data[i:i + COMMENTS_PER_BATCH]
                comments_to_analyze = []
                
                for c_data in batch_data:
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
                    comments_to_analyze.append({"id": cid, "text": comment.text})

                # Gemini Call
                batch_results = sentiment_service.analyze_comment_batch(comments_to_analyze, video_id, f"b_{i}")

                for res in batch_results.get("results", []):
                    c = db.query(Comment).filter(Comment.id == res["comment_id"]).first()
                    if c:
                        c.sentiment = SentimentType(res["sentiment"])
                        c.vader_score = res["score"]
                        c.emoji_detected = 1 if res.get("emoji", False) else 0

                processed_count += len(batch_data)
                db.commit()

                # Yield Progress
                yield f"data: {json.dumps({'status': 'processing', 'progress': processed_count, 'total': total_comments})}\n\n"

                if i + COMMENTS_PER_BATCH < total_comments:
                    time.sleep(THROTTLE_DELAY)

            # 3. Finalize
            analytics = AnalyticsService(db)
            final_comments = db.query(Comment).filter(Comment.video_id == video_id).all()
            total_score = 0.0
            total_weight = 0.0
            for c in final_comments:
                val = c.vader_score if c.vader_score is not None else 0.0
                w = 1.0 + c.like_count
                total_score += val * w
                total_weight += w
            
            if total_weight > 0:
                video.sentiment_score = total_score / total_weight
            
            video.analysis_status = "completed"
            db.commit()

            channel = db.query(Channel).filter(Channel.id == video.channel_id).first()
            if channel:
                channel.health_score = analytics.calculate_health_score(channel.id)
                db.commit()

            final_data = {
                "status": "completed",
                "video": {"id": video.id, "sentiment_score": video.sentiment_score},
                "health_score": channel.health_score if channel else 0.0,
                "insights": analytics.generate_video_insights(video_id),
                "distribution": analytics.calculate_video_sentiment_distribution(video_id)
            }
            yield f"data: {json.dumps(final_data)}\n\n"

        except Exception as e:
            print(f"SSE Error: {e}")
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(analysis_stream(), media_type="text/event-stream")

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
