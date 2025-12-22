import google.generativeai as genai
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline
import torch

class LocalSentimentService:
    def __init__(self):
        print("--- INITIALIZING SENTIMENT SERVICE ---")
        
        # 1. Initialize VADER (Fast, Rule-based, Good for social media slang)
        self.vader = SentimentIntensityAnalyzer()
        self.gemini_model = None
        
        # 🚀 CUSTOM: Add Tanglish/Hinglish/Indian Slang to VADER Lexicon
        # ... (Keeping existing lexicon updates) ...
        new_words = {
            # Tamil / Tanglish
            'semma': 4.0, 'mass': 4.0, 'verithanam': 4.0, 'thala': 2.0, 'thalapathy': 2.0,
            'kidu': 3.0, 'adipoli': 3.0, 'super': 3.0, 'vera': 2.0, 'level': 2.0,
            'mokka': -3.0, 'kevalam': -4.0, 'waste': -3.0, 'worst': -4.0, 'blade': -2.0,
            
            # Telugu / Tinglish
            'kiraak': 4.0, 'keka': 4.0, 'adurs': 4.0, 'chindhi': 3.0,
            'rod': -4.0, 'bokka': -4.0, 'daridram': -4.0,
            
            # Hindi / Hinglish
            'mast': 4.0, 'bhaval': 4.0, 'kadak': 3.0, 'op': 4.0, 'gajab': 4.0,
            'bekar': -3.0, 'ghatya': -4.0, 'bakwas': -4.0,
            
            # General Internet Slang (sometimes missed)
            'fire': 3.0, 'lit': 3.0, 'mid': -1.0, 'peak': 3.0, 'goated': 4.0,

            # Additional observed words
            'papam': -2.0, # pity/sad
            'poyindi': -2.0, # gone/lost
            'pilla': 0.0, # girl (neutral context usually)
            'love': 4.0, # ensure high weight
            'rcb': 2.0, # fans usually say positive things
            'gelichindi': 4.0, # won
            'jai': 3.0, # victoria/hail
        }
        self.vader.lexicon.update(new_words)
        print(f"VADER Initialized with {len(new_words)} custom Tanglish concepts.")

        # 2. Initialize Gemini (If API Key Available)
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
                print("Gemini 2.0 Flash Initialized for Sentiment Analysis.")
            except Exception as e:
                print(f"Failed to initialize Gemini: {e}")

        self.classifier = None # Deprecated BERT

    def analyze_comment(self, comment_text: str):
        """
        STRICT Emoji-Aware Sentiment Analysis for a single comment.
        """
        import re
        result = {
            "final_sentiment": "neutral",
            "final_score": 0.0,
            "vader": {"sentiment": "neutral", "score": 0.0},
            "gemini": {"sentiment": "neutral", "score": 0.0, "available": False},
            "emoji_detected": False,
            "topics": []
        }

        # 1. Emoji Detection
        emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)
        emojis = emoji_pattern.findall(comment_text)
        result["emoji_detected"] = len(emojis) > 0

        # Topic extraction
        words = re.findall(r'\b\w{4,}\b', comment_text.lower())
        stop_words = {'this', 'that', 'with', 'from', 'have', 'your', 'about', 'really', 'there', 'they'}
        result["topics"] = list(set([w for w in words if w not in stop_words]))[:3]

        # 2. VADER Baseline
        vader_scores = self.vader.polarity_scores(comment_text)
        vader_compound = vader_scores['compound']
        
        v_sentiment = "neutral"
        if vader_compound >= 0.05: v_sentiment = "positive"
        elif vader_compound <= -0.05: v_sentiment = "negative"
        result["vader"] = {"sentiment": v_sentiment, "score": vader_compound}

        # 3. Gemini (If available)
        if self.gemini_model:
            try:
                prompt = (
                    "Analyze sentiment for this comment independently. Interpret emojis as sentiment signals. "
                    "If a comment contains ONLY emojis, infer sentiment from them. "
                    "Classify as: positive, neutral, or negative. Assign a score between -1.0 and +1.0. "
                    "Extract 1-3 key topics. Output JSON ONLY.\n\n"
                    f"Format: {{\"sentiment\": \"label\", \"score\": 0.0, \"topics\": [\"topic1\"]}}\n\n"
                    f"Comment: \"{comment_text}\""
                )
                response = self.gemini_model.generate_content(prompt)
                try:
                    import json
                    g_data = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group())
                    result["gemini"] = {
                        "sentiment": g_data.get("sentiment", "neutral"),
                        "score": float(g_data.get("score", 0.0)),
                        "available": True
                    }
                    result["topics"] = list(set(result["topics"] + g_data.get("topics", [])))[:3]
                    result["final_sentiment"] = result["gemini"]["sentiment"]
                    result["final_score"] = result["gemini"]["score"]
                except:
                    result["final_sentiment"] = v_sentiment
                    result["final_score"] = vader_compound
            except Exception as e:
                print(f"Gemini Error: {e}")
                result["final_sentiment"] = v_sentiment
                result["final_score"] = vader_compound
        else:
            result["final_sentiment"] = v_sentiment
            result["final_score"] = vader_compound

        return result

    def analyze_comment_batch(self, comments_list: list, video_id: str, batch_id: str):
        """
        Rate-Limit-Safe Batched Analysis.
        Processes up to 5 comments in a single Gemini call.
        """
        import re
        import json

        result_batch = {
            "video_id": video_id,
            "batch_id": batch_id,
            "results": []
        }

        if not self.gemini_model:
            # Fallback to VADER for all if Gemini is down
            for c in comments_list:
                ana = self.analyze_comment(c["text"])
                result_batch["results"].append({
                    "comment_id": c["id"],
                    "sentiment": ana["final_sentiment"],
                    "score": ana["final_score"],
                    "emoji": ana["emoji_detected"]
                })
            return result_batch

        # Construct Batched Prompt
        batch_prompt = (
            "Perform emoji-aware sentiment analysis on the following batch of YouTube comments. "
            "For each comment, interpret emojis as sentiment signals. "
            "Labels: positive | neutral | negative. Score: -1.0 to 1.0. "
            "If a comment is ONLY emojis, infer sentiment from them. "
            "Return JSON ONLY. No summaries. No markdown blocks.\n\n"
            "Output Format:\n"
            "{\n"
            "  \"video_id\": \"<v_id>\",\n"
            "  \"batch_id\": \"<b_id>\",\n"
            "  \"results\": [\n"
            "    {\"comment_id\": \"id\", \"sentiment\": \"label\", \"score\": 0.0, \"emoji\": true|false}\n"
            "  ]\n"
            "}\n\n"
            "Comments to analyze:\n"
        )
        
        comments_payload = []
        for c in comments_list:
            comments_payload.append({"id": c["id"], "text": c["text"]})
        
        batch_prompt += json.dumps(comments_payload)

        try:
            response = self.gemini_model.generate_content(batch_prompt)
            try:
                # Use regex to find the JSON block in case of conversational fluff
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    g_data = json.loads(json_match.group())
                    # Validate results against requested IDs to ensure Gemini didn't hallucinate/skip
                    g_results = {r["comment_id"]: r for r in g_data.get("results", [])}
                    
                    for c in comments_list:
                        if c["id"] in g_results:
                            result_batch["results"].append(g_results[c["id"]])
                        else:
                            # Fallback for missing items in batch response
                            ana = self.analyze_comment(c["text"])
                            result_batch["results"].append({
                                "comment_id": c["id"],
                                "sentiment": ana["final_sentiment"],
                                "score": ana["final_score"],
                                "emoji": ana["emoji_detected"]
                            })
                else:
                    raise ValueError("No JSON found in response")
            except Exception as e:
                print(f"Batch Parsing Error: {e}")
                # Fallback to individual analysis if batch response is malformed
                for c in comments_list:
                    ana = self.analyze_comment(c["text"])
                    result_batch["results"].append({
                        "comment_id": c["id"],
                        "sentiment": ana["final_sentiment"],
                        "score": ana["final_score"],
                        "emoji": ana["emoji_detected"]
                    })
        except Exception as e:
            print(f"Batch Gemini Error: {e}")
            for c in comments_list:
                ana = self.analyze_comment(c["text"])
                result_batch["results"].append({
                    "comment_id": c["id"],
                    "sentiment": ana["final_sentiment"],
                    "score": ana["final_score"],
                    "emoji": ana["emoji_detected"]
                })

        return result_batch

