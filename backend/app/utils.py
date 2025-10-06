import re
from pathlib import Path
import random

# Very simple emotion picker based on keywords - replace with a model if you like.
EMOTION_MAP = {
    "happy": ["congrat", "great", "happy", "nice", "awesome"],
    "explaining": ["explain", "because", "therefore", "in summary", "first", "second"],
    "thinking": ["let me think", "hmm", "thinking", "consider"],
    "neutral": []
}

def pick_emotion(text: str) -> str:
    txt = text.lower()
    for emotion, keywords in EMOTION_MAP.items():
        for kw in keywords:
            if kw in txt:
                return emotion
    # fallback random soft emotion or neutral
    return random.choice(["neutral","explaining"])
