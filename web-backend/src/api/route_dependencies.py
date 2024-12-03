from google.cloud import storage, firestore
from src.api.util.security import validate_jwt, validate_user
from src.environment import (
    PROJECT_ID,
    DATABASE_ID,
    FIRESTORE_USER_COLLECTION,
    PROJECT_ID,
    DATABASE_ID,
    ENVIRONMENT,
    EXPECTED_AUDIENCE,
    PROJECT_ID,
    DATABASE_ID,
    BUCKET_NAME,
)

validate_token = validate_jwt(EXPECTED_AUDIENCE, ENVIRONMENT)
validate_usr = validate_user(
    PROJECT_ID,
    DATABASE_ID,
    FIRESTORE_USER_COLLECTION,
    EXPECTED_AUDIENCE,
    ENVIRONMENT,
    True,
)



# Initialize Firestore and Storage clients
db = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)

storage_client = storage.Client(project=PROJECT_ID)

bucket = storage_client.bucket(BUCKET_NAME)
