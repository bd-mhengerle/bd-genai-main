from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum
from fastapi import File, UploadFile

# Chat models
class ChatCreateRequest(BaseModel):
    name: str
#    tags: List[str]


class Chat(BaseModel):
    id: str
    name: str
    createdAt: datetime
    updatedAt: datetime
    isDeleted: bool
    favorite: bool
    files: List[str]
    tags: List[str]
    createdById: str
    history: List[str]


class UpdateChatModel(BaseModel):
    name: Optional[str]
    tags: Optional[List[str]]


class AskChatModel(BaseModel):
    question: Optional[str]
    knowledge_base_ids: Optional[List[str]]
    model:  Optional[str] = "gemini-1.5-pro"


## Knowledgebase models


class KnowledgeBaseCreateRequest(BaseModel):
    name: str
    public: bool


class KnowledgeBaseUpdateRequest(BaseModel):
    name: str
    public: bool


class KnowledgeBaseAddFilesRequest(BaseModel):
    files: List[UploadFile] = File(...)

class KnowledgeBaseRemoveFilesRequest(BaseModel):
    file_ids: List[str]


class BasicListResponse(BaseModel):
    data: List[dict]

class BasicResponse(BaseModel):
    data: dict

class UserMsgEvaluation(str, Enum):
    NOT_ANSWER = 'NO_ANSWER'
    GOOD = 'GOOD'
    BAD = 'BAD'

class ChatMessage(BaseModel):
    role: str
    content: str
    id: str
    createdAt: datetime
    userEvaluation: UserMsgEvaluation
    model: str
    tokenNumber: int