from src.api.route_dependencies import validate_usr, db
from typing import Annotated
from fastapi import Depends, APIRouter, HTTPException
from src.environment import FIRESTORE_USER_COLLECTION
from src.api.util.firestore_utils import (
    fix_firestore_dates,
)
router = APIRouter()

@router.get("/user/me")
async def health_check(user_data: Annotated[dict, Depends(validate_usr)]):
    result = db.collection(FIRESTORE_USER_COLLECTION).document(user_data["user_id"]).get()
    if not result.exists:
       raise HTTPException(status_code=404, detail="User not found")

    return {"data": fix_firestore_dates(result.to_dict())}
