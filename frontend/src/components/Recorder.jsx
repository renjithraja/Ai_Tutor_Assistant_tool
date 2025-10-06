import React, { useState } from "react";
import { stt } from "../api";

export default function Recorder({ onTranscribed }) {
  const [recording, setRecording] = useState(false);
  const [recorder, setRecorder] = useState(null);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    const chunks = [];

    mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
    mediaRecorder.onstop = async () => {
      const blob = new Blob(chunks, { type: "audio/webm" });
      const file = new File([blob], "recording.webm", { type: "audio/webm" });

      const { text } = await stt(file);
      onTranscribed(text);
    };

    mediaRecorder.start();
    setRecorder(mediaRecorder);
    setRecording(true);
  };

  const stopRecording = () => {
    recorder.stop();
    setRecording(false);
  };

  return (
    <button
      onClick={recording ? stopRecording : startRecording}
      className="p-2 bg-blue-500 text-white rounded-xl"
    >
      {recording ? "Stop 🎙️" : "Record 🎤"}
    </button>
  );
}
