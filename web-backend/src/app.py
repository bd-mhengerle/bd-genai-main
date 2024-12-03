from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.health import router as health_router
from src.api.fileupload import router as fileupload_router
from src.api.chat import router as chat_router
from src.api.knowledgebase import router as kb_router
from src.api.reporting import router as reports_router
from src.api.user import router as user_router
from src.environment import ALLOWED_ORIGINS
import logging
import os


if os.environ.get("DEBUG"):
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

app = FastAPI()
origins = [
    ALLOWED_ORIGINS,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(fileupload_router)
app.include_router(chat_router)
app.include_router(kb_router)
app.include_router(reports_router)
app.include_router(user_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
