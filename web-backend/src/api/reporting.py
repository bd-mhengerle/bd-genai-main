from fastapi import Depends, APIRouter, Query
from src.models.models import BasicListResponse
from src.api.util.firestore_utils import (
    apply_filters,
    apply_orders_by,
    fix_firestore_dates,
    apply_cursor,
)
from src.api.route_dependencies import validate_usr, db
from src.environment import (
    FIRESTORE_USER_ACTIVITY_COLLECTION,
    FIRESTORE_NEW_CHAT_RECORD_COLLECTION,
    FIRESTORE_NEW_MSG_RECORD_COLLECTION,
    FIRESTORE_NEW_UPLOAD_RECORD_COLLECTION,
    FIRESTORE_NEW_KB_RECORD_COLLECTION,
    FIRESTORE_NEW_RESUMED_CHAT_RECORD_COLLECTION,
)
from typing import List, Optional
from fastapi import HTTPException
from typing import Annotated
from google.cloud.firestore_v1 import aggregation
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


from fastapi import APIRouter

router = APIRouter()


def check_user_access(user_data: dict):
    return


def execute_listing(
    collection,
    user_data,
    filters,
    limit,
    order_by,
    cursor,
):
    check_user_access(user_data)
    ref = (
        db.collection(collection)
        .where("isDeleted", "==", False)
        .order_by("updatedAt", "DESCENDING")
        .limit(limit)
    )
    ref = apply_filters(ref, filters)

    ref = apply_orders_by(ref, order_by)

    ref = apply_cursor(ref, collection, cursor)

    records = ref.get()

    return {"data": [fix_firestore_dates(e.to_dict()) for e in records]}


def execute_sum_aggregation(user_data: dict, collection: str, filters: List[str]):
    check_user_access(user_data)
    collection_ref = db.collection(collection)
    if not filters or len(filters) <= 0:
        filters = [f"createdAt:<=:{datetime.now()}"]
    query = apply_filters(collection_ref, filters)
    aggregate_query = aggregation.AggregationQuery(query)
    aggregate_query.count(alias="total")
    results = aggregate_query.get()
    final_result = {"total": None, "read_time": None}
    for result in results:
        final_result = {
            f"{result[0].alias}": result[0].value,
            "read_time": result[0].read_time,
        }
    return final_result


@router.get("/report/user-activity")
async def report_user_activity(
    user_data: Annotated[dict, Depends(validate_usr)],
    cursor: Optional[str] = Query(None, description="Document ID to start after"),
    limit: int = Query(50, description="Number of results to return"),
    order_by: List[str] = Query(
        ["createdAt:desc"],
        description="Fields to order by. Array of the form [name:asc, name:desc]",
    ),
    filters: Optional[List[str]] = Query(
        None, description="Filters to apply, e.g., name:startswith:chat"
    ),
):
    try:
        return execute_listing(
            FIRESTORE_USER_ACTIVITY_COLLECTION,
            user_data,
            filters,
            limit,
            order_by,
            cursor,
        )
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/new-chats")
async def report_new_chats(
    user_data: Annotated[dict, Depends(validate_usr)],
    cursor: Optional[str] = Query(None, description="Document ID to start after"),
    limit: int = Query(50, description="Number of results to return"),
    order_by: List[str] = Query(
        ["createdAt:desc"],
        description="Fields to order by. Array of the form [name:asc, name:desc]",
    ),
    filters: Optional[List[str]] = Query(
        None, description="Filters to apply, e.g., name:startswith:chat"
    ),
):
    try:
        return execute_listing(
            FIRESTORE_NEW_CHAT_RECORD_COLLECTION,
            user_data,
            filters,
            limit,
            order_by,
            cursor,
        )
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/msgs")
async def report_msgs(
    user_data: Annotated[dict, Depends(validate_usr)],
    cursor: Optional[str] = Query(None, description="Document ID to start after"),
    limit: int = Query(50, description="Number of results to return"),
    order_by: List[str] = Query(
        ["createdAt:desc"],
        description="Fields to order by. Array of the form [name:asc, name:desc]",
    ),
    filters: Optional[List[str]] = Query(
        None, description="Filters to apply, e.g., name:startswith:chat"
    ),
):
    try:
        return execute_listing(
            FIRESTORE_NEW_MSG_RECORD_COLLECTION,
            user_data,
            filters,
            limit,
            order_by,
            cursor,
        )
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/uploads")
async def report_uploads(
    user_data: Annotated[dict, Depends(validate_usr)],
    cursor: Optional[str] = Query(None, description="Document ID to start after"),
    limit: int = Query(50, description="Number of results to return"),
    order_by: List[str] = Query(
        ["createdAt:desc"],
        description="Fields to order by. Array of the form [name:asc, name:desc]",
    ),
    filters: Optional[List[str]] = Query(
        None, description="Filters to apply, e.g., name:startswith:chat"
    ),
):
    try:
        return execute_listing(
            FIRESTORE_NEW_UPLOAD_RECORD_COLLECTION,
            user_data,
            filters,
            limit,
            order_by,
            cursor,
        )
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/resumed-chats")
async def report_resumed_chats(
    user_data: Annotated[dict, Depends(validate_usr)],
    cursor: Optional[str] = Query(None, description="Document ID to start after"),
    limit: int = Query(50, description="Number of results to return"),
    order_by: List[str] = Query(
        ["createdAt:desc"],
        description="Fields to order by. Array of the form [name:asc, name:desc]",
    ),
    filters: Optional[List[str]] = Query(
        None, description="Filters to apply, e.g., name:startswith:chat"
    ),
):
    try:
        return execute_listing(
            FIRESTORE_NEW_RESUMED_CHAT_RECORD_COLLECTION,
            user_data,
            filters,
            limit,
            order_by,
            cursor,
        )
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/new-kbs")
async def report_new_kbs(
    user_data: Annotated[dict, Depends(validate_usr)],
    cursor: Optional[str] = Query(None, description="Document ID to start after"),
    limit: int = Query(50, description="Number of results to return"),
    order_by: List[str] = Query(
        ["createdAt:desc"],
        description="Fields to order by. Array of the form [name:asc, name:desc]",
    ),
    filters: Optional[List[str]] = Query(
        None, description="Filters to apply, e.g., name:startswith:chat"
    ),
):
    try:
        return execute_listing(
            FIRESTORE_NEW_KB_RECORD_COLLECTION,
            user_data,
            filters,
            limit,
            order_by,
            cursor,
        )
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/aggregation/count/new-chats")
async def aggregation_report_new_chats(
    user_data: Annotated[dict, Depends(validate_usr)],
    filters: Optional[List[str]] = Query(
        None, description="Filters to apply, e.g., name:startswith:chat"
    ),
):
    return execute_sum_aggregation(
        user_data, FIRESTORE_NEW_CHAT_RECORD_COLLECTION, filters
    )


@router.get("/report/aggregation/count/msgs")
async def aggregation_report_msgs(
    user_data: Annotated[dict, Depends(validate_usr)],
    filters: Optional[List[str]] = Query(
        None, description="Filters to apply, e.g., name:startswith:chat"
    ),
):
    return execute_sum_aggregation(
        user_data, FIRESTORE_NEW_MSG_RECORD_COLLECTION, filters
    )


@router.get("/report/aggregation/count/uploads")
async def aggregation_report_uploads(
    user_data: Annotated[dict, Depends(validate_usr)],
    filters: Optional[List[str]] = Query(
        None, description="Filters to apply, e.g., name:startswith:chat"
    ),
):
    return execute_sum_aggregation(
        user_data, FIRESTORE_NEW_UPLOAD_RECORD_COLLECTION, filters
    )


@router.get("/report/aggregation/count/new-kbs")
async def aggregation_report_new_kbs(
    user_data: Annotated[dict, Depends(validate_usr)],
    filters: Optional[List[str]] = Query(
        None, description="Filters to apply, e.g., name:startswith:chat"
    ),
):
    return execute_sum_aggregation(
        user_data, FIRESTORE_NEW_KB_RECORD_COLLECTION, filters
    )


@router.get("/report/aggregation/count/resumed-chats")
async def aggregation_report_resumed_chats(
    user_data: Annotated[dict, Depends(validate_usr)],
    filters: Optional[List[str]] = Query(
        None, description="Filters to apply, e.g., name:startswith:chat"
    ),
):
    return execute_sum_aggregation(
        user_data, FIRESTORE_NEW_RESUMED_CHAT_RECORD_COLLECTION, filters
    )
