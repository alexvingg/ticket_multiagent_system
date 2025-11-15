from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ChatRequest(BaseModel):
    message: str = Field(..., description="Mensagem do usuário")
    session_id: Optional[str] = Field(default="default", description="ID da sessão")

class ChatResponse(BaseModel):
    response: str
    agent_used: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Ticket(BaseModel):
    ticket_number: str
    status: str
    body: str
    owner: str