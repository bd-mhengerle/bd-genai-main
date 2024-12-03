import os

# the name of the collection storing the chat history objects
HISTORY_COLLECTION = "chat_sessions"

PROJECT_NAME = "bd-genai-internal"
# the name of the upstream firestore database
DB_NAME = "bd-genai-firestore"


# service account json file location
dirname = os.path.dirname(__file__)
SERVICE_ACCOUNT_FILE = os.path.join(dirname, "service_account.json")
