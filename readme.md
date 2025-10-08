🎓 AI Tutor

AI Tutor is an intelligent voice-based assistant that allows users to interact with an AI model through speech. The user can speak their question, and the system provides real-time voice-based AI responses using advanced LLM and TTS technologies.

This project includes both a backend (FastAPI) and a frontend, enabling seamless speech-to-text, AI response generation, and text-to-speech functionality.

🚀 Features

🎙️ Voice Input – Speak your question directly to the AI Tutor.

🧠 AI-Powered Responses – Uses Groq LLM (Llama 3.1 8B) for intelligent and fast replies.

🔊 Voice Output – Generates AI responses in human-like speech using Coqui TTS.

💾 ChromaDB Integration – For storing embeddings and retrieval-augmented generation (RAG).

🌐 Full Stack Setup – Includes both backend (FastAPI) and frontend (React/Vite).


⚙️ Setup Instructions
1️⃣ Clone the Repository
git clone https://github.com/renjithraja/Ai_Tutor_Assistant_tool
cd ai-tutor

2️⃣ Setup the Backend
cd backend

Create Virtual Environment
python -m venv venv

Activate the Virtual Environment

Windows:

venv\Scripts\activate


Mac/Linux:

source venv/bin/activate

Install Dependencies
pip install -r requirements.txt

3️⃣ Create the .env File

Inside the backend folder, create a file named .env with the following content:

# LLM provider settings (use one or both)
GROQ_API_KEY="Replace_your_groq_key"
GROQ_MODEL=llama-3.1-8b-instant
RAG_TEMPERATURE=0.2
RAG_MAX_TOKENS=512

# Chroma DB storage location
CHROMA_DB_DIR=./chroma_db

# TTS model (coqui)
COQUI_TTS_MODEL=tts_models/en/vctk/vits

# Server
BACKEND_PORT=8000

4️⃣ Run the Backend
python -m uvicorn app.main:app --reload


Your backend will start running on:

http://127.0.0.1:8000

5️⃣ Run the Frontend

In another terminal, navigate to the frontend directory:

cd frontend
npm install
npm run dev


Then open the URL shown in your terminal (usually http://localhost:5173/) to start using the AI Tutor.

🧠 Technologies Used
Component	Technology
Backend	FastAPI, Uvicorn
Frontend	React.js / Vite
LLM Provider	Groq (Llama 3.1 8B Instant)
Database	ChromaDB
TTS Engine	Coqui TTS
Environment Management	Python venv, dotenv
🎯 How It Works

The user speaks a question using the mic.

The backend processes the audio and converts it to text.

The LLM (Groq) generates a context-aware answer.

The response is converted to speech using Coqui TTS.

The frontend plays the AI’s voice response.

📢 Example Usage

Ask: “What is machine learning?”

AI Tutor responds in voice: “Machine learning is a subset of AI that enables computers to learn from data without explicit programming.”

🧰 Requirements

Python 3.9+

Node.js 16+

Active Internet Connection

GROQ API Key

🧑‍💻 Author

👨‍💻 Renjith R
🎓 MCA Graduate | AI/ML Enthusiast | Django & Python Developer
📧 renjithraja496@gmail.com

[Visit My LinkedIn](https://www.linkedin.com/in/renjith-r)
