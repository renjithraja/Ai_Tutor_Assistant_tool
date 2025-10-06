import websocket
import json
import os

def on_message(ws, message):
    if isinstance(message, bytes):
        # Save audio chunk to file
        with open("output.wav", "ab") as f:
            f.write(message)
        print("🎵 Received audio chunk...")
    else:
        data = json.loads(message)
        if "error" in data:
            print("❌ Error:", data["error"])
        elif data.get("event") == "end":
            print("✅ Audio streaming complete! Saved as output.wav")
        else:
            print("ℹ️ Message:", data)

def on_error(ws, error):
    print("❌ WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print("🔒 WebSocket closed", close_status_code, close_msg)

def on_open(ws):
    print("✅ Connected to TTS WebSocket")
    # Example TTS request
    tts_request = {
        "text": "Hello! This is a test from FastAPI TTS WebSocket.",
        "voice": "alloy"  # Optional; depends on Coqui model
    }
    ws.send(json.dumps(tts_request))

if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        "ws://localhost:8000/ws/tts",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()
