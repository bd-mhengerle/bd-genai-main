from fastapi import APIRouter

router = APIRouter()

'''returns the health check of service'''
@router.get("/health")
async def health_check():
    return {"health": "ok"}
