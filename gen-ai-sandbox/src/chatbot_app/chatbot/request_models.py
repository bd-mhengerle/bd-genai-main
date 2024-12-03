from pydantic import BaseModel
from typing import List, Optional
from .settings import LlmIds

class ChatMessage(BaseModel):
    role: str
    content: str

class KbActive(BaseModel):
    id: str
    tool_type: List[str]

class ChatRequest(BaseModel):
    session_id: str
    user_query: str
    message_history: List[ChatMessage]
    kbs: List[KbActive]
    ai_model: Optional[str] = LlmIds.GEMINI_PRO.value


class FileUploadRequest(BaseModel):
    kb_id: str
    file_id: str
    gcs_uri: str

class FileDeleteRequest(BaseModel):
    kb_id: str
    file_id: str
    gcs_uri: str