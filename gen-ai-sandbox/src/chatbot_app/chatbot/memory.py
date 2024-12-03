from enum import Enum
from typing import List, Dict, Optional

from llama_index.core.memory import ChatMemoryBuffer
from pydantic import BaseModel

from google.cloud import firestore

from .configs import firestore_config, retriever_config


class MessageRole(str, Enum):
    """
    Represents the role of a message in the chatbot conversation.

    Attributes:
        USER: Represents a message from the user.
        ASSISTANT: Represents a message from the chatbot assistant.
    """

    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """
    Represents a chat message.

    Attributes:
        role (MessageRole): The role of the message (i.e., user or assistant).
        content (str): The content of the message.
        additional_kwargs (dict, optional): Additional keyword arguments for the message (default: {}).
    """

    role: MessageRole
    content: str
    additional_kwargs: dict = dict()


def create_memory_buffer(message_history: List[Optional[Dict]]) -> ChatMemoryBuffer:
    """
    Creates a ChatMemoryBuffer object and populates it with messages from the given message history.

    Args:
        message_history (list): A list of dictionaries representing the message history. Each dictionary should have
                                the keys 'role' and 'content', where 'role' can be either 'user' or 'assistant', and
                                'content' represents the content of the message. E.g.
                                [{'role':'assistant','content':'Hello!'},
                                {'role':'user','content':'How do I fix the robot's knee?'}]

    Returns:
        ChatMemoryBuffer: The populated ChatMemoryBuffer object.

    """
    # Create ChatMemoryBuffer
    memory = ChatMemoryBuffer(
        token_limit=retriever_config.MEMORY_TOKEN_LIMIT
    )  # Adjust token_limit as needed
    # Construct and add messages to memory
    for history in message_history:
        if history["role"] == "user":
            memory.put(ChatMessage(content=history["content"], role=MessageRole.USER))
        elif history["role"] == "assistant":
            memory.put(
                ChatMessage(content=history["content"], role=MessageRole.ASSISTANT)
            )

    return memory


def load_memory_from_firestore(chat_id: str) -> ChatMemoryBuffer:
    """
    This function requires a chat session identifier to load the session
    from Firestore.

    We assume that the firestore collection is indexed by chat session
    ID and contains a 'history' field with an object matching the format
    laid out in the create_memory_buffer function.
    :param chat_id: chat session uuid
    :return: LlamaIndex Memory Object
    """
    db = firestore.Client.from_service_account_json(
        firestore_config.SERVICE_ACCOUNT_FILE, database=firestore_config.DB_NAME
    )

    session_doc = (
        db.collection(firestore_config.HISTORY_COLLECTION).document(chat_id).get()
    )
    if session_doc.exists:
        try:
            history_dict = session_doc.to_dict()["history"]
            return create_memory_buffer(history_dict)
        except ValueError:
            print(
                "Firestore object does not contain required 'history' field and cannot be read."
            )
            return create_memory_buffer([])
