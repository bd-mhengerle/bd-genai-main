import os
from os.path import join, dirname
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.environ.get("PROJECT_ID") 

DATABASE_ID = os.environ.get("DATABASE_ID") 

GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

##################################################################################################################

FIRESTORE_FILES_COLLECTION = os.environ.get("FIRESTORE_FILES_COLLECTION") #Todo: add default

FIRESTORE_CHAT_SESSION_COLLECTION = os.environ.get("FIRESTORE_CHAT_SESSION_COLLECTION") #Todo: add default

FIRESTORE_TAGS_COLLECTION = os.environ.get("FIRESTORE_TAGS_COLLECTION") #Todo: add default

FIRESTORE_USER_COLLECTION = os.environ.get("FIRESTORE_USER_COLLECTION") #Todo: add default

FIRESTORE_KB_COLLECTION = os.environ.get("FIRESTORE_KB_COLLECTION") #Todo: add default

FIRESTORE_NEW_CHAT_RECORD_COLLECTION = os.environ.get("FIRESTORE_NEW_CHAT_RECORD_COLLECTION") #Todo: add default

FIRESTORE_NEW_MSG_RECORD_COLLECTION = os.environ.get("FIRESTORE_NEW_MSG_RECORD_COLLECTION") #Todo: add default

FIRESTORE_NEW_UPLOAD_RECORD_COLLECTION = os.environ.get("FIRESTORE_NEW_UPLOAD_RECORD_COLLECTION") #Todo: add default

FIRESTORE_NEW_KB_RECORD_COLLECTION = os.environ.get("FIRESTORE_NEW_KB_RECORD_COLLECTION") #Todo: add default

FIRESTORE_NEW_RESUMED_CHAT_RECORD_COLLECTION = os.environ.get("FIRESTORE_NEW_RESUMED_CHAT_RECORD_COLLECTION") #Todo: add default

FIRESTORE_USER_ACTIVITY_COLLECTION = os.environ.get("FIRESTORE_USER_ACTIVITY_COLLECTION") #Todo: add default

##################################################################################################################

BUCKET_NAME = os.environ.get("BUCKET_NAME") #Todo: add default!

ALLOWED_FILE_TYPES = os.environ.get("ALLOWED_FILE_TYPES")

MAX_UPLOAD_SIZE = os.environ.get("MAX_UPLOAD_SIZE")

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS")

EXPECTED_AUDIENCE = os.environ.get("EXPECTED_AUDIENCE")

ENVIRONMENT = os.environ.get("ENVIRONMENT")

GENAI_SANDBOX_API = os.environ.get("GENAI_SANDBOX_API")

PEOPLE_API_KEY = os.environ.get("PEOPLE_API_KEY")
