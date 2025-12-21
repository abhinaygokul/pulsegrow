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
