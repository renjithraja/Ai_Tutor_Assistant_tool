import os
import asyncio
import logging
from typing import List, Dict, AsyncGenerator, Optional

# Logging setup
logger = logging.getLogger("rag_service")

# ------------------------
# Groq client
# ------------------------
try:
    from groq import Groq
except ImportError:
    Groq = None

# ------------------------
# OpenAI client (fallback)
# ------------------------
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# ------------------------
# LangChain vectorstore
# ------------------------
try:
    from langchain_community.embeddings import SentenceTransformerEmbeddings
    from langchain_community.vectorstores import Chroma
except ImportError:
    try:
        from langchain.embeddings import SentenceTransformerEmbeddings
        from langchain.vectorstores import Chroma
    except ImportError:
        SentenceTransformerEmbeddings = None
        Chroma = None

# ------------------------
# Config
# ------------------------
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")

# ✅ Updated model defaults
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")  # Supported Groq model
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

TEMPERATURE = float(os.getenv("RAG_TEMPERATURE", "0.2"))
MAX_TOKENS = int(os.getenv("RAG_MAX_TOKENS", "512"))


class RagService:
    def __init__(self, chroma_dir: str = CHROMA_DIR):
        groq_key = os.getenv("GROQ_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        # ------------------------
        # Choose provider (Groq preferred)
        # ------------------------
        if groq_key and Groq:
            self.client = Groq(api_key=groq_key)
            self.provider = "groq"
            self.model_name = GROQ_MODEL
        elif openai_key and OpenAI:
            self.client = OpenAI(api_key=openai_key)
            self.provider = "openai"
            self.model_name = OPENAI_MODEL
        else:
            raise RuntimeError("❌ No valid LLM provider found. Set GROQ_API_KEY or OPENAI_API_KEY.")

        self.temperature = TEMPERATURE
        self.max_tokens = MAX_TOKENS

        # ------------------------
        # Initialize embeddings + vectorstore
        # ------------------------
        self.embedding = None
        self.db = None
        if SentenceTransformerEmbeddings and Chroma:
            try:
                self.embedding = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
                self.db = Chroma(
                    collection_name="ai_tutor",
                    embedding_function=self.embedding,
                    persist_directory=chroma_dir,
                )
            except Exception as e:
                logger.warning(f"⚠️ Vector DB init failed: {e}")
                self.db = None

        logger.info(f"✅ RAG initialized with provider={self.provider}, model={self.model_name}")

    # ------------------------
    # Context Retrieval
    # ------------------------
    def _retrieve_context(self, query: str, k: int = 4) -> str:
        if not self.db:
            return ""
        try:
            docs = self.db.similarity_search(query, k=k)
            return "\n\n".join(d.page_content for d in docs if getattr(d, "page_content", None))
        except Exception as e:
            logger.warning(f"Context retrieval failed: {e}")
            return ""

    # ------------------------
    # Build Chat Messages
    # ------------------------
    def _build_messages(self, query: str, history: List[Dict], context: Optional[str]) -> List[Dict]:
        system_msg = (
            "You are an expert, patient AI tutor. "
            "Explain concepts clearly, step-by-step, and use context when available."
        )
        messages = [{"role": "system", "content": system_msg}]
        if context:
            messages.append({"role": "system", "content": f"Context:\n{context}"})

        for m in history[-8:]:
            role = "assistant" if m.get("role") == "assistant" else "user"
            messages.append({"role": role, "content": m.get("text", "")})

        messages.append({"role": "user", "content": query})
        return messages

    # ------------------------
    # Extract Model Response
    # ------------------------
    def _extract_content(self, resp) -> str:
        try:
            if self.provider == "groq":
                choices = getattr(resp, "choices", None) or resp.get("choices")
                if choices:
                    c0 = choices[0]
                    if hasattr(c0, "message"):
                        return getattr(c0.message, "content", "")
                    if isinstance(c0, dict):
                        return c0.get("message", {}).get("content", "")
            elif self.provider == "openai":
                return resp.choices[0].message.content
        except Exception:
            pass
        return str(resp)

    # ------------------------
    # Non-Streaming Answers
    # ------------------------
    def answer_single(self, query: str) -> str:
        context = self._retrieve_context(query)
        messages = self._build_messages(query, history=[], context=context)

        try:
            if self.provider == "groq":
                resp = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            else:  # OpenAI
                resp = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                )
            return self._extract_content(resp).strip()
        except Exception as e:
            logger.error(f"❌ Error generating answer: {e}")
            return "Sorry, I couldn't process your request right now."

    def answer_with_history(self, query: str, history: List[Dict]) -> str:
        context = self._retrieve_context(query)
        messages = self._build_messages(query, history=history, context=context)

        try:
            if self.provider == "groq":
                resp = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            else:
                resp = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                )
            return self._extract_content(resp).strip()
        except Exception as e:
            logger.error(f"❌ Error generating contextual answer: {e}")
            return "I'm having trouble retrieving the information right now."

    # ------------------------
    # Streaming (Groq Only)
    # ------------------------
    async def stream_answer_with_history(self, query: str, history: List[Dict]) -> AsyncGenerator[str, None]:
        if self.provider != "groq":
            yield self.answer_with_history(query, history)
            return

        context = self._retrieve_context(query)
        messages = self._build_messages(query, history=history, context=context)

        loop = asyncio.get_event_loop()

        def blocking_stream():
            return self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )

        try:
            stream = await loop.run_in_executor(None, blocking_stream)
            for chunk in stream:
                try:
                    delta = getattr(chunk.choices[0], "delta", {}).get("content")
                    if delta:
                        yield delta
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"❌ Streaming failed: {e}")
            yield "Sorry, I encountered a problem while streaming the response."
