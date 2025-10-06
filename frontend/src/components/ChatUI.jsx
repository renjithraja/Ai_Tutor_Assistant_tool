import React, { useEffect, useRef, useState } from "react";
import { connectWS } from "../api";
import Recorder from "./Recorder";
import Mascot from "./Mascot";

export default function ChatUI() {
  const [messages, setMessages] = useState([]);
  const [ws, setWs] = useState(null);
  const [finalResponse, setFinalResponse] = useState(null);

  useEffect(() => {
    const socket = connectWS("demo");
    socket.onopen = () => console.log("✅ WebSocket connected");
    socket.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === "start") {
        setMessages((prev) => [...prev, { role: "assistant", text: "" }]);
      } else if (data.type === "token") {
        setMessages((prev) => {
          const copy = [...prev];
          copy[copy.length - 1].text += data.text;
          return copy;
        });
      } else if (data.type === "final") {
        setFinalResponse({ text: data.text, emotion: data.emotion });
      }
    };
    setWs(socket);
    return () => socket.close();
  }, []);

  const sendMessage = (msg) => {
    setMessages((prev) => [...prev, { role: "user", text: msg }]);
    ws.send(JSON.stringify({ query: msg }));
  };

  return (
    <div className="p-4">
      <div className="h-80 overflow-y-auto border rounded-lg p-2 bg-gray-50">
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <span
              className={`inline-block px-3 py-1 rounded-xl m-1 ${
                m.role === "user"
                  ? "bg-blue-500 text-white"
                  : "bg-gray-200 text-black"
              }`}
            >
              {m.text}
            </span>
          </div>
        ))}
      </div>
      <div className="mt-4 flex gap-2">
        <Recorder onTranscribed={sendMessage} />
      </div>
      {finalResponse && (
        <Mascot text={finalResponse.text} emotion={finalResponse.emotion} />
      )}
    </div>
  );
}
