# app/emotion.py
def detect_emotion(text: str) -> str:
    """
    Dummy emotion detection (replace with ML later).
    """
    if any(word in text.lower() for word in ["sad", "upset", "tired"]):
        return "empathetic"
    elif any(word in text.lower() for word in ["happy", "excited", "great"]):
        return "cheerful"
    return "neutral"
