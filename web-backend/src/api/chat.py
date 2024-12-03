from fastapi import Depends, APIRouter, Header
from src.models.models import (
    BasicListResponse,
    ChatCreateRequest,
    ChatMessage,
    UpdateChatModel,
    AskChatModel,
)
from src.api.util.firestore_utils import (
    apply_cursor,
    apply_filters,
    apply_orders_by,
    fix_firestore_dates,
)
from src.api.util.proxy import send_request_genai_sandbox
from src.api.route_dependencies import validate_token, validate_usr, db
from src.environment import (
    FIRESTORE_CHAT_SESSION_COLLECTION,
    FIRESTORE_KB_COLLECTION,
)
from src.api.util.user_activity import (
    new_chat_creation,
    new_question_asked,
    chat_resumed,
    update_token_usage,
)
from typing import List, Optional
from fastapi import HTTPException, Query
from google.cloud import firestore
from typing import Annotated
from datetime import datetime, timezone
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(validate_token)])


def format_message_history(e: ChatMessage):
    return {
        "role": e.role,
        "content": f"{e.content}",
    }


@router.post("/chat")
async def create_chat(
    chat_request: ChatCreateRequest, user_data: Annotated[dict, Depends(validate_usr)]
):
    try:
        user_id = user_data["user_id"]
        email = user_data["email"]

        kb_ref = db.collection(FIRESTORE_KB_COLLECTION).document()
        chat_doc_ref = db.collection(FIRESTORE_CHAT_SESSION_COLLECTION).document()

         # Prepare kb for chat
        kb_data = {
            "id": kb_ref.id,
            "name": chat_request.name,
            "isDeleted": False,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "public": False,
            "filesIds": [],
            "createdBy": { "email": "system", "id": chat_doc_ref.id},
            "createdById": chat_doc_ref.id,
            "tools": ["pinecone"],
            "type": "chat-default",
            "referenceId": kb_ref.id,
        }
        # Prepare the chat document data
        chat_data = {
            "id": chat_doc_ref.id,
            "name": chat_request.name,
            "kbId": kb_ref.id,
            "isDeleted": False,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "favorite": False,
            "createdBy": {"id": user_id, "email": email},
            "createdById": user_id,
            "history": [],
        }
        # Save the documents
        chat_doc_ref.set(chat_data)
        kb_ref.set(kb_data)
        # User Activity
        new_chat_creation(chat_doc_ref.id, user_id, email)
        return {
            "message": "Chat created successfully",
            "data": fix_firestore_dates(chat_doc_ref.get().to_dict()),
        }
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/listing", response_model=BasicListResponse)
async def get_chats(
    user_data: Annotated[dict, Depends(validate_usr)],
    cursor: Optional[str] = Query(None, description="Document ID to start after"),
    limit: int = Query(50, description="Number of results to return"),
    order_by: List[str] = Query(
        ["createdAt:desc"],
        description="Fields to order by. Array of the form [name:asc, name:desc]",
    ),
    filters: Optional[List[str]] = Query(
        None, description="Filters to apply, e.g., name:startswith:chat"
    ),
):
    try:
        ref = (
            db.collection(FIRESTORE_CHAT_SESSION_COLLECTION)
            .where("isDeleted", "==", False)
            .where(
                "createdById", "==", user_data["user_id"]
            )  # Only fetch chats for the current user
            .limit(limit)
        )
        ref = apply_filters(ref, filters)

        ref = apply_orders_by(ref, order_by)

        ref = apply_cursor(ref, FIRESTORE_CHAT_SESSION_COLLECTION, cursor)

        records = ref.get()

        return {"data": [fix_firestore_dates(e.to_dict()) for e in records]}

    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/{id}")
async def get_chat(id: str):
    try:
        chat_ref = db.collection(FIRESTORE_CHAT_SESSION_COLLECTION).document(id)
        chat_doc = chat_ref.get()

        if not chat_doc.exists:
            raise HTTPException(status_code=404, detail="Chat not found")
        return chat_doc.to_dict()
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/chat/{id}")
async def update_chat(id: str, update_data: UpdateChatModel):
    try:
        chat_ref = db.collection(FIRESTORE_CHAT_SESSION_COLLECTION).document(id)
        chat_doc = chat_ref.get()

        # Check if document exists and is not deleted
        if not chat_doc.exists or chat_doc.get("isDeleted"):
            raise HTTPException(
                status_code=404, detail="Chat not found or has been deleted"
            )

        update_dict = update_data.dict(exclude_unset=True)
        if not update_dict:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        chat_ref.update(update_dict)

        updated_chat_doc = chat_ref.get()
        updated_chat = updated_chat_doc.to_dict()

        return updated_chat
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/{id}")
async def delete_chat(id: str):
    try:
        chat_ref = db.collection(FIRESTORE_CHAT_SESSION_COLLECTION).document(id)
        chat_doc = chat_ref.get()

        # Check if document exists
        if not chat_doc.exists:
            raise HTTPException(status_code=404, detail="Chat not found")

        chat_ref.update({"isDeleted": True})

        return {"deleted": True}

    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/{id}/favorite")
async def toggle_favorite(id: str):
    try:
        chat_ref = db.collection(FIRESTORE_CHAT_SESSION_COLLECTION).document(id)
        chat_doc = chat_ref.get()

        # Check if document exists
        if not chat_doc.exists:
            raise HTTPException(status_code=404, detail="Chat not found")

        # Get the current favorite status
        chat_data = chat_doc.to_dict()
        current_favorite = chat_doc.get("favorite")

        # Toggle the favorite status
        new_favorite = not current_favorite

        chat_ref.update({"favorite": new_favorite})

        return {"favorite": new_favorite}

    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/{id}/ask")
async def ask(
    id: str,
    ask_request: AskChatModel,
    user_data: Annotated[dict, Depends(validate_usr)],
):
    user_id = user_data["user_id"]
    email = user_data["email"]

    kbs_doc = []
    if len(ask_request.knowledge_base_ids) >= 1:
        kbs_doc = (
            db.collection(FIRESTORE_KB_COLLECTION)
            .where("__name__", "in", ask_request.knowledge_base_ids)
            .get()
        )
        ids_docs = [e.id for e in kbs_doc]
        for kb_id in ask_request.knowledge_base_ids:
            if kb_id not in ids_docs:
                raise HTTPException(status_code=400, detail="Invalid KBs")

    chat_ref = db.collection(FIRESTORE_CHAT_SESSION_COLLECTION).document(id)
    chat_doc = chat_ref.get()
    # Check if document exists
    if not chat_doc.exists:
        raise HTTPException(status_code=404, detail="Chat not found")

    try:
        new_message_at = datetime.now(timezone.utc)
        kbs_request = [
            {"id": e.get("referenceId"), "tool_type": e.get("tools") or ["pinecone"]} for e in kbs_doc
        ]
        chat = chat_doc.to_dict()
        chat_history = chat_doc.get("history") or []
        data = {
            "session_id": id,
            "user_query": ask_request.question,
            "message_history": [
                format_message_history(ChatMessage(**e)) for e in chat_history
            ],
            "kbs": kbs_request,
            "ai_model": ask_request.model,  # TODO: check with tuma to see if this is the name of the value used in the message.
        }
        logger.debug(f"ask_chat.data {data}")
        try:
            result = send_request_genai_sandbox("chat", "POST", data)
            logger.debug(result)
        except Exception as e:
            logger.warning(e)
            result = {
                "data": {
                    "id": str(uuid.uuid4()),
                    "content": "Unexpected error",
                    "citations": None,
                    "tokenNumber": 0,
                }
            }
        response = result["data"]
        new_response_message_at = datetime.now(timezone.utc)
        logger.debug(f"ask_chat.send_request_genai_sandbox {result}")
        # Update chat HIstory:
        user_question = {
            "role": "user",
            "content": ask_request.question,
            "id": str(uuid.uuid4()),
            "createdAt": new_message_at,
            "userEvaluation": "NO_ANSWER",
            "model": ask_request.model,
            "citations": None,
            "tokenNumber": 0,  # TODO: Add corresponding value here
            "kbIds": kbs_request,
        }
        model_response = {
            "role": "assistant",
            "content": response["content"],
            "userEvaluation": "NO_ANSWER",  # NO_ANSWER, GOOD, BAD
            "id": str(uuid.uuid4()),
            "createdAt": new_response_message_at,
            "model": ask_request.model,
            "tokenNumber": response[
                "tokenNumber"
            ],  # TODO: Add corresponding value here
            "citations": response["citations"],
            "kbIds": kbs_request,
        }
        # Update chat history
        chat_history.append(user_question)
        chat_history.append(model_response)
        chat_ref.update({"history": chat_history})
        # User Activity
        new_question_asked(
            id,
            user_question["content"],
            user_question["id"],
            model_response["content"],
            model_response["id"],
            model_response["tokenNumber"],
            ask_request.model,
            kbs_request,
            user_id,
            email,
        )
        chat_resumed(id, chat["updatedAt"], user_id, email)
        update_token_usage(response["tokenNumber"], ask_request.model, user_id, email)
        return {"data": model_response}
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))
