from backend.database import SessionLocal
from backend.models.models import Video, Channel

db = SessionLocal()
videos = db.query(Video).all()
channels = db.query(Channel).all()

print(f"Channels: {len(channels)}")
for c in channels:
    print(f" - {c.title} ({c.id})")

print(f"Videos: {len(videos)}")
for v in videos:
    print(f" - {v.title} ({v.id}) linked to {v.channel_id}")
