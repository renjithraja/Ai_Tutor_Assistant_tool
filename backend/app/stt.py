# app/stt.py
import os
from typing import Optional

try:
    from faster_whisper import WhisperModel
except Exception as e:
    raise ImportError("Please install faster-whisper: pip install faster-whisper. Error: " + str(e))

# Model choice: small by default; change via WHISPER_MODEL env var
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
# Device: "cuda" if available, else "cpu". You can override with WHISPER_DEVICE env var.
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cuda" if os.getenv("CUDA_VISIBLE_DEVICES") else "cpu")

# Initialize a module-level model (load once)
_whisper_model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE)

def transcribe_audio_file(file_path: str, language: Optional[str] = "en") -> str:
    """
    Transcribe audio file to text using faster-whisper.
    Returns the transcript string.
    """
    # faster-whisper returns segments, info
    segments, info = _whisper_model.transcribe(file_path, language=language, beam_size=5)
    texts = []
    for seg in segments:
        # segment has .text attribute
        texts.append(seg.text)
    return " ".join(texts).strip()
