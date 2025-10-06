from pydantic import BaseModel
from typing import Optional

class QueryRequest(BaseModel):
    query: str

class ChatRequest(BaseModel):
    session_id: str
    query: str
