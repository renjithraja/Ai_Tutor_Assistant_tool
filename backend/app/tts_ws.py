import os
import uuid
import tempfile
import asyncio
from fastapi import APIRouter, WebSocket

# Try Coqui TTS
try:
    from TTS.api import TTS as CoquiTTS
    _coqui_available = True
except Exception:
    _coqui_available = False

# Fallback to pyttsx3
try:
    import pyttsx3
    _pyttsx3_available = True
except Exception:
    _pyttsx3_available = False


router = APIRouter()

# Initialize Coqui model once
coqui_tts = None
if _coqui_available:
    model_name = os.getenv("COQUI_TTS_MODEL", "tts_models/en/vctk/vits")
    try:
        # Try with phonemes (default)
        coqui_tts = CoquiTTS(model_name=model_name)
    except Exception as e:
        print(f"[TTS] Warning: failed with phonemes: {e}")
        print("[TTS] Retrying with use_phonemes=False ...")
        try:
            coqui_tts = CoquiTTS(model_name=model_name, progress_bar=False, gpu=False)
            # Force-disable phonemes if supported by API
            if hasattr(coqui_tts, "use_phonemes"):
                coqui_tts.use_phonemes = False
        except Exception as e2:
            print(f"[TTS] Coqui TTS completely failed: {e2}")
            coqui_tts = None


@router.websocket("/ws/tts")
async def websocket_tts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time TTS.
    - Client sends JSON: {"text": "...", "voice": "..."}
    - Server responds with audio bytes in small chunks.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            text = data.get("text", "")
            voice = data.get("voice", None)

            if not text.strip():
                await websocket.send_json({"error": "Empty text"})
                continue

            # Generate audio file
            out_path = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex}.wav")

            if _coqui_available and coqui_tts:
                try:
                    coqui_tts.tts_to_file(text=text, speaker=voice, file_path=out_path)
                except Exception as e:
                    await websocket.send_json({"error": f"TTS failed: {str(e)}"})
                    continue

            elif _pyttsx3_available:
                engine = pyttsx3.init()
                engine.save_to_file(text, out_path)
                engine.runAndWait()
            else:
                await websocket.send_json({"error": "No TTS backend installed"})
                continue

            # Stream file back in chunks
            with open(out_path, "rb") as f:
                while chunk := f.read(4096):
                    await websocket.send_bytes(chunk)

            # Notify end of audio
            await websocket.send_json({"event": "end"})
            os.remove(out_path)

    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()
