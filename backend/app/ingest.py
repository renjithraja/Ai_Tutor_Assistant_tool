import os
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import TextLoader
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma

CHROMA_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_db")

def ingest_text_file(path: str, collection_name: str = "ai_tutor"):
    loader = TextLoader(path, encoding="utf-8")
    docs = loader.load()
    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    embedding = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma(collection_name=collection_name, embedding_function=embedding, persist_directory=CHROMA_DIR)
    db.add_documents(chunks)
    db.persist()
    return len(chunks)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    args = p.parse_args()
    c = ingest_text_file(args.file)
    print(f"Ingested {c} chunks")
