from functools import wraps
from typing import Annotated
import logging
import jwt
from fastapi import Depends, HTTPException, Header, Request
from google.auth.transport import requests
from google.cloud import firestore
from src.environment import PEOPLE_API_KEY
import google.oauth2.id_token
import requests as python_request



logger = logging.getLogger(__name__)

def cache(func):
    cached_results = {}

    @wraps(func)
    def wrapper(*args, **kwargs):
        if args in cached_results:
            return cached_results[args]
        else:
            result = func(*args, **kwargs)
            if result:
                cached_results[args] = result
            return result

    return wrapper


def validate_jwt(expected_audience: str, environment: str):
    logger.debug(f"expected audience: {expected_audience}")
    def decode_jwt(request: Request, x_goog_iap_jwt_assertion: Annotated[str | None, Header()] = None, authorization: Annotated[str | None, Header()] = None):
            logger.debug(f"Request headers: {request.headers}")
            decoded_jwt = {}
            try:
                if environment == "production":
                    logger.debug(f"decoding x_goog_iap_jwt_assertion: {x_goog_iap_jwt_assertion}")
                    decoded_jwt = google.oauth2.id_token.verify_token(
                        x_goog_iap_jwt_assertion,
                        requests.Request(),
                        audience=expected_audience,
                        certs_url="https://www.gstatic.com/iap/verify/public_key",
                    )
                else:
                    logger.debug(f"decoding authorization token: {authorization}")
                    id_token = authorization.split()[-1]
                    decoded_jwt = jwt.decode(id_token, options={"verify_signature": False})
                return decoded_jwt
                
            except Exception as ex:
                logger.exception(str(ex))
                raise HTTPException(status_code=401, detail=f"Unauthorized")

    return decode_jwt

def validate_user(
        project: str,
        firestore_instance: str, 
        user_collection: str,
        expected_audience: str,
        environment: str,
        process_user: bool
    ):
    dependency = validate_jwt(expected_audience, environment)
    logger.debug(f"JWT validated")
    def get_or_create_user(decoded_jwt: Annotated[dict, Depends(dependency)]):
        if process_user:
            user_id = decoded_jwt['sub'].split(':')[-1]
            email = decoded_jwt['email']
            #if environment == "production": #Not necessary since we are using google provider
            #    email = email.split(":")[-1]
            logger.debug(f"Processing user {user_id}")

            if not user_exists_in_firestore(project, firestore_instance, user_collection, user_id):

                # request_info_url = f"https://content-people.googleapis.com/v1/people/{user_id}?personFields=photos,names&key={PEOPLE_API_KEY}"

                # sending get request and saving the response as response object
                # r = python_request.get(url = request_info_url)

                # extracting data in json format
                # data = r.json()

                # logger.debug(f"Response content-people: {data}")

                client = firestore.Client(project=project, database=firestore_instance)
                user_data = {
                    'id': user_id, 
                    'email':email,
                    'createdAt': firestore.SERVER_TIMESTAMP,
                    'updatedAt': firestore.SERVER_TIMESTAMP
                }
                client.collection(user_collection).document(user_id).set(user_data)
                logger.info(f"User {user_id} created in firestore")

            decoded_jwt['user_id'] = user_id
        else:
            logger.info("Not processing user")
            decoded_jwt['user_id'] = decoded_jwt['sub'].split(':')[-1]

        return decoded_jwt

    return get_or_create_user

@cache
def user_exists_in_firestore(project, firestore_instance, collection, id):
    client = firestore.Client(project=project, database=firestore_instance)
    return client.collection(collection).document(id).get().exists