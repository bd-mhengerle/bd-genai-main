from pydantic import BaseModel
from typing import List
from google.cloud import firestore
from src.api.route_dependencies import db
from src.environment import (
    FIRESTORE_USER_ACTIVITY_COLLECTION,
    FIRESTORE_NEW_CHAT_RECORD_COLLECTION,
    FIRESTORE_NEW_MSG_RECORD_COLLECTION,
    FIRESTORE_NEW_UPLOAD_RECORD_COLLECTION,
    FIRESTORE_NEW_KB_RECORD_COLLECTION,
    FIRESTORE_NEW_RESUMED_CHAT_RECORD_COLLECTION,
)
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

valid_models = [
    "model1",
    "model2",
    "model3",
]  # TODO: Change to actual values. ASK TUMA OR BRODY


####################################################################################################
################# GRANULAR ACTIVITY TRACKING #################
####################################################################################################


def create_new_chat_record(chat_id: str, user_id: str):
    collection = db.collection(FIRESTORE_NEW_CHAT_RECORD_COLLECTION)
    doc_ref = collection.document()
    if not doc_ref.get().exists:
        data = {
            "userId": user_id,
            "isDeleted": False,
            "chatId": chat_id,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
        doc_ref.set(data)

    return doc_ref


def create_new_msg_record(
    chat_id: str | None,
    question: str,
    questionId: str,
    response: str,
    responseId: str,
    token_usage: int,
    model: str,
    kbs: List[dict],
    user_id: str,
):
    collection = db.collection(FIRESTORE_NEW_MSG_RECORD_COLLECTION)
    doc_ref = collection.document()
    if not doc_ref.get().exists:
        doc_ref.set({
            "userId": user_id,
            "isDeleted": False,
            "question": question,
            "questionId": questionId,
            "response": response,
            "responseId": responseId,
            "chatId": chat_id,
            "tokenUsage": token_usage,
            "tokenCost": 0, # Calculate cost
            "model": model,
            "kbsIds": kbs,
            "createdAt": firestore.SERVER_TIMESTAMP,  # type: ignore
            "updatedAt": firestore.SERVER_TIMESTAMP,
        })

    return doc_ref


def create_new_upload_record(kb_id: str, file_id: str, size_bytes: int, user_id: str):
    collection = db.collection(FIRESTORE_NEW_UPLOAD_RECORD_COLLECTION)
    doc_ref = collection.document()
    if not doc_ref.get().exists:
        data = {
            "userId": user_id,
            "isDeleted": False,
            "fileId": file_id,
            "kbId": kb_id,  # Might be null
            "sizeBytes": size_bytes,
            "createdAt": firestore.SERVER_TIMESTAMP,  # type: ignore
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
        doc_ref.set(data)

    return doc_ref


def create_new_kb_record(kb_id: str, user_id: str):
    collection = db.collection(FIRESTORE_NEW_KB_RECORD_COLLECTION)
    doc_ref = collection.document()
    if not doc_ref.get().exists:
        data = {
            "userId": user_id,
            "isDeleted": False,
            "kbId": kb_id,
            "createdAt": firestore.SERVER_TIMESTAMP,  # type: ignore
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
        doc_ref.set(data)

    return doc_ref


def create_resume_chat_record(chat_id: str, user_id: str):
    collection = db.collection(FIRESTORE_NEW_RESUMED_CHAT_RECORD_COLLECTION)
    doc_ref = collection.document()
    if not doc_ref.get().exists:
        data = {
            "userId": user_id,
            "isDeleted": False,
            "chatId": chat_id,  # Might be null
            "createdAt": firestore.SERVER_TIMESTAMP,  # type: ignore
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
        doc_ref.set(data)

    return doc_ref


####################################################################################################
################# USER GENERAL ACTIVITY TABLE #################
####################################################################################################


def create_if_does_not_exist_user_activity(user_id, user_email):
    collection = db.collection(FIRESTORE_USER_ACTIVITY_COLLECTION)
    doc_ref = collection.document(user_id)
    if not doc_ref.get().exists:
        collection.document(user_id).set({
            "id": user_id,
            "email": user_email,
            "name": "user_name_tbd",
            "isDeleted": False,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "newChat": 0,
            "questionsAsked": 0,
            "chatsResumed": 0,
            "documentsUploaded": 0,
            "knowledgeBaseCreated": 0,
            "documentsUploadTotalSizeBytes": 0,
            "lastMessageAt": None,
            "lastCreatedChatAt": None,
            "lastResumedChatAt": None,
            "lastDocumentUploadedAt": None,
            "lastKnowledgeBaseCreatedAt": None,
            "tokensUsed": {"model1": 0, "model2": 0, "model3": 0},
        })

    return collection.document(user_id)


def new_chat_creation(chat_id: str, user_id: str, user_email: str):
    try:
        doc_ref = create_if_does_not_exist_user_activity(user_id, user_email)
        doc_ref.update(
            {
                "newChat": firestore.Increment(1),
                "lastCreatedChatAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            }
        )
        create_new_chat_record(chat_id, user_id)
        return True
    except Exception as e:
        logger.error(f"[new_chat_creation.error]: {e}")
        return False


def new_question_asked(
    chat_id: str,
    question: str,
    questionId: str,
    response: str,
    responseId: str,
    token_number,
    model: str,
    kbs: List[dict],
    user_id: str,
    user_email: str,
):
    try:
        doc_ref = create_if_does_not_exist_user_activity(user_id, user_email)
        doc_ref.update(
            {
                "questionsAsked": firestore.Increment(1),
                "lastMessageAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            }
        )
        create_new_msg_record(
            chat_id,
            question,
            questionId,
            response,
            responseId,
            token_number,
            model,
            kbs,
            user_id,
        )
        return True
    except Exception as e:
        logger.error(f"[new_question_asked.error]: {e}")
        return False


def chat_resumed(
    chat_id: str, chat_created_at: datetime, user_id: str, user_email: str
):
    try:
        now = datetime.now(timezone.utc)

        diff = now - chat_created_at

        minutes = (diff.seconds % 3600) // 60

        if (
            minutes >= 30
        ):  # If more or equal than 30min has passed since the last time this chat was used we say it was resumed
            doc_ref = create_if_does_not_exist_user_activity(user_id, user_email)
            doc_ref.update(
                {
                    "chatsResumed": firestore.Increment(1),
                    "lastResumedChatAt": firestore.SERVER_TIMESTAMP,
                    "updatedAt": firestore.SERVER_TIMESTAMP,
                }
            )
            create_resume_chat_record(chat_id, user_id)
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"[chat_resumed.error]: {e}")
        return False


def document_uploaded(
    file_id: str, kb_id: str, size_bytes: int, user_id: str, user_email: str
):
    try:
        doc_ref = create_if_does_not_exist_user_activity(user_id, user_email)
        doc_ref.update(
            {
                "documentsUploaded": firestore.Increment(1),
                "lastDocumentUploadedAt": firestore.SERVER_TIMESTAMP,
                "uploadsTotalSizeBytes": firestore.Increment(size_bytes),
                "updatedAt": firestore.SERVER_TIMESTAMP,
            }
        )
        create_new_upload_record(kb_id, file_id, size_bytes, user_id)
        return True
    except Exception as e:
        logger.error(f"[document_uploaded.error]: {e}")
        return False


def new_kb_created(kb_id: str, user_id: str, user_email: str):
    try:
        doc_ref = create_if_does_not_exist_user_activity(user_id, user_email)
        doc_ref.update(
            {
                "knowledgeBaseCreated": firestore.Increment(1),
                "lastKnowledgeBaseCreatedAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            }
        )
        create_new_kb_record(kb_id, user_id)
        return True
    except Exception as e:
        logger.error(f"[new_kb_created.error]: {e}")
        return False


def update_token_usage(model: str, tokenNumber: int, user_id: str, user_email: str):
    try:
        if model is not valid_models:
            return False
        doc_ref = create_if_does_not_exist_user_activity(user_id, user_email)
        doc_ref.update(
            {
                f"tokensUsed.{model}": firestore.Increment(tokenNumber),
                "updatedAt": firestore.SERVER_TIMESTAMP,
            }
        )
        return
    except Exception as e:
        logger.error(f"[update_token_usage.error]: {e}")
        return False
