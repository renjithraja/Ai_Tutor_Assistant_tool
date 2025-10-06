import React, { useEffect } from "react";
import { tts } from "../api";

export default function Mascot({ text, emotion }) {
  useEffect(() => {
    if (!text) return;
    (async () => {
      const url = await tts(text);
      const audio = new Audio(url);
      audio.play();
    })();
  }, [text]);

  return (
    <div className="p-4 flex flex-col items-center">
      <div className="text-6xl">
        {emotion === "happy" && "😃"}
        {emotion === "sad" && "😢"}
        {emotion === "angry" && "😡"}
        {emotion === "neutral" && "🙂"}
      </div>
      <p className="mt-2 text-lg text-gray-700">{text}</p>
    </div>
  );
}
