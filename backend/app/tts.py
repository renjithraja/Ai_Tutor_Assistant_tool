import os
import tempfile
import uuid

# Try Coqui TTS first
try:
    from TTS.api import TTS as CoquiTTS
    _coqui_available = True
except Exception:
    _coqui_available = False

# pyttsx3 fallback
try:
    import pyttsx3
    _pyttsx3_available = True
except Exception:
    _pyttsx3_available = False


def synthesize_tts(text: str, voice: str = None) -> str:
    """
    Generate TTS audio file from `text`. Returns path to generated WAV file.
    - Uses Coqui TTS (multi-speaker if available)
    - Falls back to pyttsx3
    """
    if not text or text.strip() == "":
        raise ValueError("Text for TTS cannot be empty.")

    out_path = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex}.wav")

    if _coqui_available:
        try:
            model_name = os.getenv("COQUI_MODEL", "tts_models/en/vctk/vits")
            tts = CoquiTTS(model_name=model_name)

            # Check available speakers
            if voice and hasattr(tts, "speakers") and voice not in tts.speakers:
                raise ValueError(f"Invalid voice. Available voices include: {tts.speakers[:5]}...")

            tts.tts_to_file(text=text, speaker=voice, file_path=out_path)
            return out_path
        except Exception as e:
            print(f"[TTS] Coqui failed: {e}")

    if _pyttsx3_available:
        engine = pyttsx3.init()
        if voice:
            voices = engine.getProperty("voices")
            for v in voices:
                if voice.lower() in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break
        engine.save_to_file(text, out_path)
        engine.runAndWait()
        return out_path

    raise RuntimeError("❌ No TTS backend available. Install Coqui TTS (`pip install TTS`) or pyttsx3.")
