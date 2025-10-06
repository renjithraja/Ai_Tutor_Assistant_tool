import os
import tempfile
import pathlib
from dotenv import load_dotenv
from typing import Optional

from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from app.models import QueryRequest, ChatRequest
from app.sessions import SessionStore
from app.utils import pick_emotion
from app.rag import RagService
from app.stt import transcribe_audio_file
from app.tts import synthesize_tts
from app import tts_ws

# ------------------------
# Setup
# ------------------------
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_tutor_backend")

app = FastAPI(
    title="AI Tutor Backend",
    version="1.0.0",
    description="AI Tutor backend powered by Groq RAG + Whisper STT + TTS + WebSockets",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach routers
app.include_router(tts_ws.router)

sessions = SessionStore()
rag: Optional[RagService] = None


# ------------------------
# Startup
# ------------------------
@app.on_event("startup")
async def startup_event():
    global rag
    try:
        rag = RagService()
        logger.info("✅ Groq RAG Service initialized successfully.")
    except Exception as e:
        logger.warning("⚠️ GROQ_API_KEY not set, RAG service unavailable.")
        rag = None


# ------------------------
# Health Check
# ------------------------
@app.get("/healthz")
async def health_check() -> dict:
    return {
        "status": "ok",
        "rag_available": rag is not None,
    }


# ------------------------
# REST Endpoints
# ------------------------
@app.post("/query")
async def query_endpoint(req: QueryRequest) -> dict:
    if not rag:
        return JSONResponse({"error": "RAG not configured. Set GROQ_API_KEY."}, status_code=500)

    text = rag.answer_single(req.query)
    emotion = pick_emotion(text)
    return {"text": text, "emotion": emotion}


@app.post("/chat")
async def chat_endpoint(req: ChatRequest) -> dict:
    if not rag:
        return JSONResponse({"error": "RAG not configured. Set GROQ_API_KEY."}, status_code=500)

    history = sessions.get_history(req.session_id)
    answer = rag.answer_with_history(req.query, history)

    sessions.append(req.session_id, {"role": "user", "text": req.query})
    sessions.append(req.session_id, {"role": "assistant", "text": answer})

    emotion = pick_emotion(answer)
    return {"text": answer, "emotion": emotion}


@app.post("/stt")
async def stt_endpoint(file: UploadFile = File(...)) -> dict:
    try:
        contents = await file.read()
        suffix = pathlib.Path(file.filename).suffix or ".wav"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        logger.info(f"🎤 STT request: {file.filename}")
        transcript = transcribe_audio_file(tmp_path)
        return {"text": transcript}

    except Exception as e:
        logger.exception("STT error")
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if 'tmp_path' in locals() and pathlib.Path(tmp_path).exists():
            os.remove(tmp_path)


@app.post("/tts")
async def tts_endpoint(payload: dict):
    text = payload.get("text", "").strip()
    if not text:
        return JSONResponse({"error": "Empty text payload"}, status_code=400)

    try:
        logger.info("🗣️ TTS request")
        audio_path = synthesize_tts(text)
    except Exception as e:
        logger.exception("TTS error")
        return JSONResponse({"error": str(e)}, status_code=500)

    def iterfile():
        with open(audio_path, "rb") as f:
            yield from f

    headers = {"Content-Disposition": "attachment; filename=response.wav"}
    return StreamingResponse(iterfile(), media_type="audio/wav", headers=headers)


# ------------------------
# WebSocket Endpoint (Chat)
# ------------------------
@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
    session_id = websocket.query_params.get("session_id") or "default"

    try:
        while True:
            payload = await websocket.receive_json()
            user_text = (payload or {}).get("query", "").strip()

            if not rag:
                await websocket.send_json({"type": "error", "message": "RAG not configured."})
                continue

            if not user_text:
                await websocket.send_json({"type": "error", "message": "Empty query"})
                continue

            logger.info(f"💬 WS chat request (session={session_id})")

            history = sessions.get_history(session_id)
            await websocket.send_json({"type": "start"})

            full_response = ""
            async for chunk in rag.stream_answer_with_history(user_text, history):
                full_response += chunk
                await websocket.send_json({"type": "token", "text": chunk})

            sessions.append(session_id, {"role": "user", "text": user_text})
            sessions.append(session_id, {"role": "assistant", "text": full_response})

            emotion = pick_emotion(full_response)
            await websocket.send_json({"type": "final", "text": full_response, "emotion": emotion})

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: session {session_id}")
    except Exception as e:
        logger.exception("WebSocket error")
        await websocket.send_json({"type": "error", "message": str(e)})


# ------------------------
# Run
# ------------------------
if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
