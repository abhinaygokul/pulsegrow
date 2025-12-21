from backend.services.sentiment_service import LocalSentimentService

service = LocalSentimentService()

test_sentences = [
    "Padam semma mass",
    "This movie is mokka",
    "Verithanam thala",
    "Simply waste time",
    "Pure rod movie",
    "Kiraak visuals"
]

print("-" * 30)
for text in test_sentences:
    result = service.analyze_comment(text)
    print(f"Text: '{text}' -> Sentiment: {result['sentiment']} (Score: {result['score']})")
print("-" * 30)
