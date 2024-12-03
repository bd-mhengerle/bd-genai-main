import logging
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Set, Optional
from google.cloud import firestore
from .configs import firestore_config
from .agent import Agent
from . import request_models
from .load_pinecone import upload_files as pc_upload_files, delete_files as pc_delete_files
import os
from datetime import datetime, timezone

# Initialize FastAPI
app = FastAPI()

# Firestore client setup
db = firestore.Client(project=firestore_config.PROJECT_NAME, database=firestore_config.DB_NAME)

class Chatbot:
    """
    A class representing a chatbot.

    This class provides methods for initializing the chatbot and submitting messages for processing.
    """

    def __init__(self):
        """
        Initializes the Chatbot object and sets up logging.
        """
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    def submit_message(
        self,
        user_query: str,
        message_history: List[request_models.ChatMessage],
        active_kbs: List[request_models.KbActive],
        model_name: str
    ) -> dict:
        """
        Submits a message to the chatbot with active knowledge bases and returns the response.

        Args:
            user_query (str): The user's query.
            message_history (List[request_models.ChatMessage]): The chat history.
            active_kbs (List[request_models.KbActive]): The list of active knowledge bases.
            model_name (str): The name of the language model to use (one of the available values in the LlmIds Enum).

        Returns:
            dict: The response from the chatbot, including output, metadata, and token count.
        """
        # Get the set of tools associated
        tool_types = set()
        kb_ids = set()
        for element in active_kbs:
            tool_types.update(element.tool_type)
            kb_ids.add(element.id)

        # Instantiate the agent with the prepared message history and active tools
        agent = Agent(
            message_history=[e.__dict__ for e in message_history],
            kb_ids=kb_ids,
            tool_types=tool_types,
            chat_model_name=model_name
        )
        # Query the agent and get the output
        output = agent.query_agent(query=user_query)

        return output


# Initialize chatbot
chatbot = Chatbot()


# API to submit a message
@app.post("/chat")
async def chat(chat_request: request_models.ChatRequest) -> dict:
    """
    API endpoint to interact with the chatbot.

    Args:
        chat_request (request_models.ChatRequest): The chat request payload including session ID, user query, and knowledge base IDs.

    Returns:
        dict: The response from the chatbot, including content, citations, and token count.
    """

    # Get the response from the chatbot with active knowledge bases and tool types
    response = chatbot.submit_message(
        user_query=chat_request.user_query,
        message_history=chat_request.message_history,
        active_kbs=chat_request.kbs,
        model_name=chat_request.ai_model
    )
    return {
        "response": {
            "content": response["output"],
            "citations": response["metadata"],
            "tokenNumber": response["count"],
        }
    }

@app.post("/upload-files")
async def upload_files(request: list[request_models.FileUploadRequest]) -> dict:
    """
    API endpoint to upload files.

    Args:
        request (list[models.FileUploadRequest]): The list of file upload requests.


    Returns:
        dict: A dictionary indicating the success status of the file upload.

    Raises:
        HTTPException: If there's an error during the file upload process.
    """
    try:
        pc_upload_files(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading files: {str(e)}")
    
    return {"successful": True}

@app.post("/delete-files")
async def delete_files(request: list[request_models.FileDeleteRequest]) -> dict:
    """
    API endpoint to delete files.

    Args:
        request (list[request_models.FileDeleteRequest]): The list of file delete requests.

    Returns:
        dict: A dictionary indicating the success status of the file deletion.

    Raises:
        HTTPException: If there's an error during the file deletion process.
    """
    try:
        pc_delete_files(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting files: {str(e)}")
    return {"successful": True}

"""returns the health check of service"""
@app.get("/health")
async def health_check() -> dict:
    """
    API endpoint to check the health status of the service.

    Returns:
        dict: A dictionary indicating the health status of the service.
    """
    return {"health": "ok"}
