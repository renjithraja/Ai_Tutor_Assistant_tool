const BACKEND_URL = "http://127.0.0.1:8000"; // change if deployed

// REST API
export async function stt(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BACKEND_URL}/stt`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}

export async function tts(text) {
  const res = await fetch(`${BACKEND_URL}/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

// WebSocket for chat
export function connectWS(sessionId = "demo") {
  const ws = new WebSocket(
    `ws://127.0.0.1:8000/ws/chat?session_id=${sessionId}`
  );
  return ws;
}
