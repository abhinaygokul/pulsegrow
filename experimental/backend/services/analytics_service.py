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
            # Base weight is 1, add log(likes + 1) to prevent huge likes from skewing too much, 
            # or just linear if per PR/FAQ "50 likes matters more than 50 comments". 
            # PR/FAQ says "Like-weighted emotional contribution".
            weight = 1.0 + comment.like_count
            
            sentiment_val = 0.0
            if comment.sentiment == SentimentType.POSITIVE:
                sentiment_val = 1.0
            elif comment.sentiment == SentimentType.NEGATIVE:
                sentiment_val = -1.0
            
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
        Generates rule-based insights since we are running locally without an LLM.
        """
        comments = self.db.query(Comment).filter(Comment.video_id == video_id).all()
        if not comments:
            return ["No comments to analyze yet."]
        
        insights = []
        
        # 1. Sentiment Dominance
        pos = sum(1 for c in comments if c.sentiment == SentimentType.POSITIVE)
        neg = sum(1 for c in comments if c.sentiment == SentimentType.NEGATIVE)
        total = len(comments)
        
        if pos / total > 0.7:
            insights.append("🌟 Overwhelmingly Positive: The audience loves this content.")
        elif neg / total > 0.4:
            insights.append("⚠️ High Negativity: This video is receiving significant criticism.")
        elif pos > 0 and neg > 0 and abs(pos - neg) < (total * 0.1):
             insights.append("⚖️ Polarizing Content: The audience is split between positive and negative reactions.")
        else:
             insights.append("💬 Balanced Discussion: Calculating sentiment spread...")

        # 2. Key Topics (Simple Frequency - Heuristic)
        # In a real local LLM setup we would use BERTopic, but here we use word freq for speed
        text = " ".join([c.text for c in comments]).lower()
        # Basic stop words 
        stop_words = set(["the", "is", "and", "to", "a", "of", "in", "it", "that", "this", "for", "on", "you", "my", "with", "video", "bro", "sir", "mam"])
        words = [w for w in text.split() if w.isalnum() and len(w) > 3 and w not in stop_words]
        
        if words:
            from collections import Counter
            common = Counter(words).most_common(3)
            topics = ", ".join([w[0] for w in common])
            insights.append(f"🔥 Hot Topics: Users are frequently mentioning: {topics}")
            
        # 3. Engagement Insight
        total_likes = sum(c.like_count for c in comments)
        if total_likes > total * 2:
            insights.append("🚀 High Engagement: Comments are generating a lot of likes/discussion.")
            
        return insights
