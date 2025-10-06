import { useState, useEffect, useRef } from "react";
import "./App.css";

function App() {
  const [listening, setListening] = useState(false);
  const [conversations, setConversations] = useState([
    {
      id: 1,
      title: "Getting Started",
      messages: [
        { role: "assistant", text: "Hello! I'm your AI tutor. How can I help you today?" }
      ],
      timestamp: new Date().toISOString()
    }
  ]);
  const [currentConversationId, setCurrentConversationId] = useState(1);
  const [status, setStatus] = useState("Idle");
  const [emotion, setEmotion] = useState("neutral");
  const [audio, setAudio] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const chatEndRef = useRef(null);
  const nextIdRef = useRef(2);

  // Get current conversation
  const currentConversation = conversations.find(c => c.id === currentConversationId);
  const chatHistory = currentConversation?.messages || [];

  // Scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  // Create new chat
  const handleNewChat = () => {
    const newConversation = {
      id: nextIdRef.current,
      title: `New Chat ${nextIdRef.current}`,
      messages: [
        { role: "assistant", text: "Hello! I'm your AI tutor. How can I help you today?" }
      ],
      timestamp: new Date().toISOString()
    };
    setConversations(prev => [newConversation, ...prev]);
    setCurrentConversationId(nextIdRef.current);
    nextIdRef.current += 1;
    setEmotion("neutral");
    setStatus("Idle");
  };

  // Switch conversation
  const handleSwitchConversation = (id) => {
    setCurrentConversationId(id);
    setEmotion("neutral");
    setStatus("Idle");
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
    }
  };

  // Delete conversation
  const handleDeleteConversation = (id, e) => {
    e.stopPropagation();
    if (conversations.length === 1) {
      alert("Cannot delete the last conversation!");
      return;
    }
    setConversations(prev => prev.filter(c => c.id !== id));
    if (currentConversationId === id) {
      setCurrentConversationId(conversations[0].id === id ? conversations[1].id : conversations[0].id);
    }
  };

  // Update conversation title based on first user message
  const updateConversationTitle = (convId, firstMessage) => {
    setConversations(prev => prev.map(conv => {
      if (conv.id === convId && conv.title.startsWith("New Chat")) {
        return {
          ...conv,
          title: firstMessage.slice(0, 30) + (firstMessage.length > 30 ? "..." : "")
        };
      }
      return conv;
    }));
  };

  // Stop response (TTS or listening)
  const handleStop = () => {
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
    }
    setListening(false);
    setStatus("Stopped");
    setEmotion("neutral");
  };

  // Microphone capture
  const handleMicClick = async () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech Recognition not supported on this browser!");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.start();

    setListening(true);
    setStatus("Listening...");
    setEmotion("listening");

    recognition.onresult = async (event) => {
      const transcript = event.results[0][0].transcript;
      setListening(false);
      setStatus("Thinking...");
      setEmotion("thinking");

      // Update current conversation with user message
      setConversations(prev => prev.map(conv => {
        if (conv.id === currentConversationId) {
          const isFirstUserMessage = conv.messages.length === 1;
          if (isFirstUserMessage) {
            updateConversationTitle(conv.id, transcript);
          }
          return {
            ...conv,
            messages: [...conv.messages, { role: "user", text: transcript }]
          };
        }
        return conv;
      }));

      await handleQuery(transcript);
    };

    recognition.onerror = (err) => {
      console.error("Speech recognition error:", err);
      setListening(false);
      setStatus("Error");
      setEmotion("sad");
    };
  };

  // Send user query to backend
  const handleQuery = async (query) => {
    try {
      const res = await fetch("http://127.0.0.1:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();

      if (data.error) {
        setConversations(prev => prev.map(conv => {
          if (conv.id === currentConversationId) {
            return {
              ...conv,
              messages: [...conv.messages, { role: "assistant", text: "Error: " + data.error }]
            };
          }
          return conv;
        }));
        setStatus("Error");
        setEmotion("sad");
        return;
      }

      // Add AI reply to current conversation
      setConversations(prev => prev.map(conv => {
        if (conv.id === currentConversationId) {
          return {
            ...conv,
            messages: [...conv.messages, { role: "assistant", text: data.text }]
          };
        }
        return conv;
      }));
      
      setEmotion(data.emotion || "happy");
      setStatus("Speaking...");

      // Text-to-Speech
      const ttsRes = await fetch("http://127.0.0.1:8000/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: data.text }),
      });

      const blob = await ttsRes.blob();
      const url = URL.createObjectURL(blob);
      const newAudio = new Audio(url);
      setAudio(newAudio);
      newAudio.play();
      newAudio.onended = () => {
        setStatus("Idle");
        setEmotion("neutral");
      };
    } catch (err) {
      console.error("API error:", err);
      setConversations(prev => prev.map(conv => {
        if (conv.id === currentConversationId) {
          return {
            ...conv,
            messages: [...conv.messages, { role: "assistant", text: "Sorry, I couldn't process your request. Please try again." }]
          };
        }
        return conv;
      }));
      setStatus("Error");
      setEmotion("sad");
    }
  };

  // Emoji for AI emotion
  const getMascotInfo = () => {
    switch (emotion) {
      case "happy":
        return { emoji: "😊", color: "#10b981", label: "Happy" };
      case "sad":
        return { emoji: "😢", color: "#ef4444", label: "Sad" };
      case "excited":
        return { emoji: "🤩", color: "#f59e0b", label: "Excited" };
      case "thinking":
        return { emoji: "🤔", color: "#8b5cf6", label: "Thinking" };
      case "listening":
        return { emoji: "👂", color: "#06b6d4", label: "Listening" };
      case "angry":
        return { emoji: "😡", color: "#ef4444", label: "Angry" };
      default:
        return { emoji: "🙂", color: "#6366f1", label: "Neutral" };
    }
  };

  const mascotInfo = getMascotInfo();

  return (
    <div className="app-container">
      
      {/* Left Sidebar - Chat History */}
      <aside className={`chat-history-sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <div className="sidebar-title">
            <span className="sidebar-icon">💬</span>
            {sidebarOpen && <h2>Chat History</h2>}
          </div>
          <button 
            className="toggle-sidebar-btn" 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
          >
            {sidebarOpen ? '◀' : '▶'}
          </button>
        </div>
        
        {sidebarOpen && (
          <>
            <button className="new-chat-button" onClick={handleNewChat}>
              <span className="new-chat-icon">➕</span>
              <span>New Chat</span>
            </button>

            <div className="conversations-container">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`conversation-card ${conv.id === currentConversationId ? 'active' : ''}`}
                  onClick={() => handleSwitchConversation(conv.id)}
                >
                  <div className="conversation-main">
                    <span className="conversation-emoji">💭</span>
                    <div className="conversation-details">
                      <h3 className="conversation-name">{conv.title}</h3>
                      <p className="conversation-meta">{conv.messages.length} messages</p>
                    </div>
                  </div>
                  <button 
                    className="delete-conversation-btn"
                    onClick={(e) => handleDeleteConversation(conv.id, e)}
                    aria-label="Delete conversation"
                  >
                    🗑️
                  </button>
                </div>
              ))}
            </div>
          </>
        )}
      </aside>

      {/* Main Content Wrapper */}
      <main className="main-wrapper">
        
        {/* Top Header Bar */}
        <header className="top-header">
          <div className="header-left-section">
            <div className="app-logo">🎓</div>
            <div className="app-info">
              <h1 className="app-title">AI Tutor Assistant</h1>
              <p className="app-subtitle">Your personal learning companion</p>
            </div>
          </div>
          
          <div className="header-right-section">
            <div className="status-indicator">
              <span className="status-text">{status}</span>
              {listening && <span className="recording-dot"></span>}
            </div>
          </div>
        </header>

        {/* Content Area with Chat and Right Sidebar */}
        <div className="content-wrapper">
          
          {/* Main Chat Area */}
          <section className="chat-container">
            <div className="messages-area">
              {chatHistory.map((msg, i) => (
                <div
                  key={i}
                  className={`message-wrapper ${msg.role}`}
                >
                  <div className="message-bubble">
                    <div className="message-header">
                      <span className="message-avatar">
                        {msg.role === "user" ? "👤" : "🤖"}
                      </span>
                      <span className="message-sender">
                        {msg.role === "user" ? "You" : "AI Tutor"}
                      </span>
                    </div>
                    <p className="message-text">{msg.text}</p>
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>
          </section>

          {/* Right Sidebar - Mascot & Status */}
          <aside className="status-sidebar">
            
            {/* Mascot Display */}
            <div className="mascot-card">
              <div className="mascot-display">
                <div className={`mascot-avatar ${emotion}`}>
                  <span className="mascot-emoji">{mascotInfo.emoji}</span>
                </div>
              </div>
              <div 
                className="mascot-emotion-tag"
                style={{ backgroundColor: mascotInfo.color }}
              >
                {mascotInfo.label}
              </div>
            </div>

            {/* Status Information */}
            <div className="info-card">
              <h3 className="info-card-title">Tutor Status</h3>
              <div className="info-list">
                <div className="info-item">
                  <span className="info-key">Mode:</span>
                  <span className="info-value" style={{ color: mascotInfo.color }}>
                    {mascotInfo.label}
                  </span>
                </div>
                <div className="info-item">
                  <span className="info-key">Messages:</span>
                  <span className="info-value">{chatHistory.length}</span>
                </div>
                <div className="info-item">
                  <span className="info-key">Status:</span>
                  <span className="info-value">{status}</span>
                </div>
              </div>
            </div>

            {/* Tips Information */}
            <div className="tips-card">
              <h3 className="tips-title">💡 Quick Tip</h3>
              <p className="tips-content">
                Click the microphone button to ask questions. I can help with homework, 
                explanations, and study tips!
              </p>
            </div>
          </aside>
        </div>

        {/* Bottom Control Panel */}
        <footer className="control-panel">
          <div className="control-buttons">
            
            {/* Microphone Button */}
            <button
              onClick={handleMicClick}
              disabled={listening}
              className={`control-btn mic-btn ${listening ? "listening" : ""}`}
            >
              <span className="btn-icon">{listening ? "🎙️" : "🎤"}</span>
              <span className="btn-text">{listening ? "Listening..." : "Start Speaking"}</span>
              {listening && (
                <div className="audio-wave">
                  <span className="wave-bar"></span>
                  <span className="wave-bar"></span>
                  <span className="wave-bar"></span>
                </div>
              )}
            </button>

            {/* Stop Button */}
            <button onClick={handleStop} className="control-btn stop-btn">
              <span className="btn-icon">⏹️</span>
              <span className="btn-text">Stop</span>
            </button>
          </div>

          {/* Footer Info */}
          <div className="footer-info">
            <p className="powered-by">
              ⚡ Powered by <strong>FastAPI</strong> · <strong>Groq</strong> · <strong>Whisper</strong> · <strong>Coqui TTS</strong>
            </p>
          </div>
        </footer>

      </main>
    </div>
  );
}

export default App;