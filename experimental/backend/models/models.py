from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from backend.database import Base
import datetime
import enum

class SentimentType(enum.Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

class Channel(Base):
    __tablename__ = "channels"

    id = Column(String, primary_key=True, index=True)  # YouTube Channel ID
    title = Column(String, index=True)
    thumbnail_url = Column(String)
    health_score = Column(Float, default=0.0) # -1.0 to 1.0
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    
    videos = relationship("Video", back_populates="channel")

class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, index=True) # YouTube Video ID
    channel_id = Column(String, ForeignKey("channels.id"))
    title = Column(String)
    thumbnail_url = Column(String)
    published_at = Column(DateTime)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    sentiment_score = Column(Float, default=0.0)
    
    channel = relationship("Channel", back_populates="videos")
    comments = relationship("Comment", back_populates="video")
    
    analysis_status = Column(String, default="pending") # pending, processing, completed, error

class Comment(Base):
    __tablename__ = "comments"

    id = Column(String, primary_key=True, index=True)
    video_id = Column(String, ForeignKey("videos.id"))
    text = Column(Text)
    author = Column(String)
    like_count = Column(Integer, default=0)
    published_at = Column(DateTime)
    
    # Analysis
    sentiment = Column(Enum(SentimentType), default=SentimentType.NEUTRAL) # Final Decision
    confidence_score = Column(Float, default=0.0)

    # Detailed Comparative Data
    # We store the raw outputs for side-by-side comparison
    vader_sentiment = Column(String, default="neutral") # "positive", "negative", "neutral"
    vader_score = Column(Float, default=0.0)
    
    gemini_sentiment = Column(String, default="neutral")
    gemini_score = Column(Float, default=0.0)
    
    video = relationship("Video", back_populates="comments")
