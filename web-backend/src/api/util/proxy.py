from pydantic import BaseModel
from src.environment import (
    GENAI_SANDBOX_API,
)
from typing import List, Optional, Any

from fastapi import HTTPException, Query
import google.auth.transport.requests
import google.oauth2.id_token
import urllib
import json
import logging
import aiohttp
import asyncio

logger = logging.getLogger(__name__)


class RequestArray(BaseModel):
    endpoint: str
    method: str
    payload: Any

class RequestArrayResults:
    response: aiohttp.ClientResponse
    request_payload: Any
    json_response: Any


async def fetch(session: aiohttp.ClientSession, url: str, data, headers):
    """Execute an http call async
    Args:
        session: contexte for making the http call
        url: URL to call
    Return:
        responses: A dict like object containing http response
    """
    async with session.post(url=url, json=data, headers=headers) as response:
        # resp = await response.json()
        return {"response": response, "request_payload": data, "json_response": await response.json()}


def exception_handler(request, exception):
    print("Request failed")


async def send_request_genai_sandbox_array(requestArray: List[dict]):
    try:
        id_token = ""
        auth_req = google.auth.transport.requests.Request()
        id_token = google.oauth2.id_token.fetch_id_token(auth_req, GENAI_SANDBOX_API)
        async with aiohttp.ClientSession(json_serialize=json.dumps) as session:
            tasks = []
            for req in requestArray:
                endpoint = req.get("endpoint")
                tasks.append(
                    fetch(
                        session,
                        f"{GENAI_SANDBOX_API}/{endpoint}",
                        req.get("payload"),
                        {
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {id_token}",
                        },
                    )
                )
            responses: List[RequestArrayResults] = await asyncio.gather(*tasks, return_exceptions=True)
        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def send_request_genai_sandbox(endpoint: str, method: str, payload: any):
    try:
        data = json.dumps(payload)
        # Convert to String
        data = str(data)
        # Convert string to byte
        final_data = data.encode("utf-8")
        id_token = ""
        auth_req = google.auth.transport.requests.Request()
        id_token = google.oauth2.id_token.fetch_id_token(auth_req, GENAI_SANDBOX_API)
        req = urllib.request.Request(
            url=f"{GENAI_SANDBOX_API}/{endpoint}", data=final_data, method="POST"
        )
        req.add_header("Authorization", f"Bearer {id_token}")
        req.add_header("Content-Type", "application/json")
        response = urllib.request.urlopen(req)
        res = json.loads(response.read())
        return {"data": res["response"]}
    except urllib.error.HTTPError as e:
        match e.code:
            case 401:
                raise HTTPException(status_code=401, detail="Unauthorized")
            case _:
                logger.exception(e)
                raise HTTPException(status_code=e.code, detail="Something went wrong")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
