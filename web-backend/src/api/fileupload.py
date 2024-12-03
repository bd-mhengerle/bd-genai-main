from fastapi import File, Form, UploadFile, HTTPException, APIRouter, Depends, Query
from src.api.util.cloud_storage import generate_download_signed_url
from fastapi.responses import JSONResponse
from google.cloud import firestore
from typing import Annotated, List, Optional
from src.api.route_dependencies import (
    validate_token,
    validate_usr,
    db,
    bucket,
)
from src.api.util.firestore_utils import (
    fix_firestore_dates,
    apply_filters,
    apply_orders_by,
    apply_cursor,
)
from src.api.util.user_activity import document_uploaded
from src.environment import (
    FIRESTORE_FILES_COLLECTION,
)
import logging
from src.models.models import BasicListResponse, BasicResponse

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(validate_token)])


def create_signed_url(doc: firestore.DocumentSnapshot):
    logger.info("Generating signed URL")
    record = doc.to_dict()
    gutil = record["gcsPath"]
    bucket = gutil.split("/")[2]
    blob_name = "/".join(gutil.split("/")[3:])
    print(blob_name)
    signed_url = generate_download_signed_url(bucket, blob_name)
    record["authenticatedURL"] = signed_url
    return fix_firestore_dates(record)


@router.get("/files/listing", response_model=BasicListResponse)
async def get_files(
    limit: int = Query(50, description="Number of items to return"),
    order_by: Optional[str] = Query(None, description="name:desc, name:asc"),
    filters: Optional[List[str]] = Query(
        None, description="Filters to apply, e.g., name:startswith:chat"
    ),
    cursor: Optional[str] = Query(
        None, description="Document snapshot cursor for pagination"
    ),
):
    try:
        ref = (
            db.collection(FIRESTORE_FILES_COLLECTION)
            .where("isDeleted", "==", False)
            .limit(limit)
        )

        ref = apply_filters(ref, filters)

        ref = apply_orders_by(ref, order_by)

        ref = apply_cursor(ref, FIRESTORE_FILES_COLLECTION, cursor)

        records = ref.get()

        return {"data": [create_signed_url(e) for e in records]}
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/signed", response_model=BasicResponse)
async def signed_url(
    blob_name: str = Query(
        None,
        description="The blob_name that is going to be signed. Sample: test-drive-sync/11wtvASfuHoLKkLr_Z_rj85BXgu80MR_V/docx_to_pdf/1UoxNq02fuKM9SNyPWZHxhdsJ2eItnf0Y.pdf",
    )
):
    try:
        valid_buckets = [
            "bd-drive-data",
            "bd-gh-data-spot-sdk",
            "bd-user-upload",
            "test-drive-sync",
        ]  # TODO: Maybe change to enviroment variables or a more dynamic way to do it
        if not blob_name:
            raise HTTPException(status_code=400, detail="Invalid blob name.")
        bucket, blob = blob_name.split("/", 1)
        if not (bucket or blob):
            raise HTTPException(
                status_code=400, detail="Invalid blob name. Invalid format"
            )
        if bucket not in valid_buckets:
            raise HTTPException(status_code=400, detail="Invalid blob name.")
        signed_url = generate_download_signed_url(bucket, blob)
        return {"data": {"authenticatedURL": signed_url}}
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))
