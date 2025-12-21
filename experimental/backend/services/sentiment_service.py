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

            # try:
            #     genai.configure(api_key=api_key)
            #     self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
            #     print("Gemini 2.0 Flash Initialized for Sentiment Analysis.")
        #     except Exception as e:
        #         print(f"Failed to initialize Gemini: {e}")
        pass

        self.classifier = None # Deprecated BERT

    def _load_transformer(self):
        if self.classifier:
            return

        try:
            print("Loading Transformer Model (Lazy Load)...")
            # We use nlptown/bert-base-multilingual-uncased-sentiment 
            # It's a robust alternative to raw MuRIL for sentiment, covering Indian languages.
            self.classifier = pipeline(
                "sentiment-analysis", 
                model="nlptown/bert-base-multilingual-uncased-sentiment",
                device=0 if torch.cuda.is_available() else -1
            )
            print("Transformer Model Loaded.")
        except Exception as e:
            print(f"Warning: Could not load Transformer model: {e}")
            self.classifier = None

    def analyze_comment(self, comment_text: str):
        result = {
            "final_sentiment": "neutral",
            "final_score": 0.0,
            "vader": {"sentiment": "neutral", "score": 0.0},
            "gemini": {"sentiment": "neutral", "score": 0.0, "available": False}
        }

        # 1. Run VADER (Always)
        clean_text = comment_text.lower()
        vader_scores = self.vader.polarity_scores(clean_text)
        vader_compound = vader_scores['compound']
        
        v_sentiment = "neutral"
        if vader_compound >= 0.05: v_sentiment = "positive"
        elif vader_compound <= -0.05: v_sentiment = "negative"
        
        result["vader"] = {"sentiment": v_sentiment, "score": vader_compound}

        # 2. Run Gemini (If Available)
        if self.gemini_model:
            try:
                response = self.gemini_model.generate_content(
                    f"Classify the sentiment of this comment as 'positive', 'neutral', or 'negative'. Return ONLY the label.\n\nComment: \"{comment_text}\""
                )
                g_text = response.text.strip().lower()
                
                g_sentiment = "neutral"
                g_score = 0.0
                if "positive" in g_text: 
                    g_sentiment = "positive"
                    g_score = 0.9
                elif "negative" in g_text: 
                    g_sentiment = "negative"
                    g_score = -0.9
                
                result["gemini"] = {"sentiment": g_sentiment, "score": g_score, "available": True}
                
                # If Gemini is available, it dictates the Final Decision
                result["final_sentiment"] = g_sentiment
                result["final_score"] = g_score

            except Exception as e:
                import traceback
                print(f"Gemini Error for comment '{comment_text[:20]}...': {e}")
                traceback.print_exc()
                print("Falling back to VADER.")
        
        # 3. Fallback Logic (if Gemini didn't run or failed)
        if not result["gemini"]["available"]:
            # Use Hybrid VADER + Transformer logic here if we wanted, 
            # but for simplicity of "Comparision" requested, we'll stick to VADER as the baseline
            # or allow the previous logic. 
            # Let's use the VADER result as final for now or the Hybrid if we re-enabled it.
            # To keep it clean for the user's specific "Compare VADER vs Gemini" request:
            result["final_sentiment"] = result["vader"]["sentiment"]
            result["final_score"] = result["vader"]["score"]

        return result
