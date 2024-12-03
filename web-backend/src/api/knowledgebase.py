from fastapi import Depends, APIRouter, Query
from fastapi import File, Form, UploadFile, HTTPException, APIRouter, Depends, Query
from src.api.util.proxy import send_request_genai_sandbox_array
from src.models.models import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseUpdateRequest,
    KnowledgeBaseAddFilesRequest,
    KnowledgeBaseRemoveFilesRequest,
)
from src.models.models import BasicListResponse
from src.api.util.firestore_utils import (
    apply_filters,
    apply_orders_by,
    fix_firestore_dates,
    apply_cursor,
)
from src.api.util.user_activity import document_uploaded
from src.api.util.user_activity import new_kb_created
from src.api.route_dependencies import validate_token, validate_usr, db, bucket
from src.environment import (
    FIRESTORE_KB_COLLECTION,
    FIRESTORE_FILES_COLLECTION,
    ALLOWED_FILE_TYPES,
    MAX_UPLOAD_SIZE,
)
from typing import List, Optional
from fastapi import HTTPException
from google.cloud import firestore
from typing import Annotated
from google.cloud.firestore_v1 import aggregation
import logging

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(validate_token)])


def check_valid_files(file_ids: List[str]):
    files_ref = (
        db.collection(FIRESTORE_FILES_COLLECTION)
        .where("id", "in", file_ids)
        .where("isDeleted", "==", False)
        .get()
    )
    if len(file_ids) != len(files_ref):
        raise HTTPException(
            status_code=400, detail=f"Invalid files are present in the request."
        )


async def upload_files(
    user_data: dict,
    kb_id: str,
    files: List[UploadFile] = File(...),
):
    try:
        total_size = 0
        file_ids = []
        user_id = user_data["user_id"]
        email = user_data["email"]
        files_data: List[dict] = []

        allowed_file_types = ALLOWED_FILE_TYPES
        if not allowed_file_types:
            raise HTTPException(
                status_code=500,
                detail="Allowed file types are not set in environment variables.",
            )
        allowed_file_types = allowed_file_types.split(",")

        max_upload_size = MAX_UPLOAD_SIZE
        if not max_upload_size:
            raise HTTPException(
                status_code=500,
                detail="Max upload size is not set in environment variables.",
            )
        max_upload_size = int(max_upload_size)

        # Validate file types and sizes
        for file in files:
            if file.content_type not in allowed_file_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type {file.content_type} is not allowed.",
                )
            file_content = await file.read()
            file_size = len(file_content)
            total_size += file_size
            if total_size > max_upload_size:
                raise HTTPException(
                    status_code=400,
                    detail="Total upload size exceeds the maximum allowed size.",
                )
            file.file.seek(0)  # Reset file pointer after reading

        for file in files:
            # Generate the `gsutil` URL
            path = f"user-uploads/{user_id}/kbs/{kb_id}/{file.filename}"
            gutil_url = f"gs://{bucket.name}/{path}"

            query = (
                db.collection(FIRESTORE_FILES_COLLECTION)
                .where("createdById", "==", user_data["user_id"])
                .where("name", "==", file.filename)
            )
            aggregate_query = aggregation.AggregationQuery(query)

            # `alias` to provides a key for accessing the aggregate query results
            aggregate_query.count(alias="total")

            results = aggregate_query.get()

            total_same_name = results[0][0].value

            if total_same_name >= 1:
                new_file_name = f"{file.filename}({int(total_same_name+1)})"
                path = f"user-uploads/{user_id}/kbs/{kb_id}/{new_file_name}"
                gutil_url = f"gs://{bucket.name}/{path}"

            # Upload file to GCS
            blob = bucket.blob(path)
            blob.upload_from_file(file.file, content_type=file.content_type)

            ref = db.collection(FIRESTORE_FILES_COLLECTION).document()

            data = {
                "id": ref.id,
                "name": file.filename,
                "mimeType": file.content_type,
                "sizeBytes": file_size,
                "gcsPath": gutil_url,
                "createdById": user_data["user_id"],
                "createdBy": {"id": user_data["user_id"], "email": user_data["email"]},
                "isDeleted": False,
                "createdById": user_data["user_id"],
                "createdAt": firestore.SERVER_TIMESTAMP,
            }
            ref.set(data)
            file_ids.append(ref.id)
            files_data.append(data)
            # User Activity!
            document_uploaded(ref.id, kb_id, file_size, user_id, email)
        return [files_data, file_ids]
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kb")
async def create_kb(
    request_data: KnowledgeBaseCreateRequest,
    user_data: Annotated[dict, Depends(validate_usr)],
):
    try:
        user_id = user_data["user_id"]
        email = user_data["email"]
        ref = db.collection(FIRESTORE_KB_COLLECTION).document()
        data = {
            "id": ref.id,
            "name": request_data.name,
            "isDeleted": False,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "public": request_data.public,
            "filesIds": [],
            "createdBy": {"id": user_id, "email": email},
            "createdById": user_id,
            "tools": ["pinecone"],
            "type": "user-uploaded",
            "referenceId": ref.id,
        }
        ref.set(data)
        # User activity
        new_kb_created(ref.id, user_id, email)
        return {
            "message": "KB created successfully",
            "data": fix_firestore_dates(ref.get().to_dict()),
        }
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kb/{id}")
async def get_kb(id: str):
    try:
        ref = db.collection(FIRESTORE_KB_COLLECTION).document(id)
        doc = ref.get()
        if not doc.exists or doc.get("isDeleted"):
            raise HTTPException(status_code=404, detail="Not found")
        return {"data": fix_firestore_dates(ref.get().to_dict())}
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/kb/{id}")
async def update_kb(id: str, request_data: KnowledgeBaseUpdateRequest):
    try:
        ref = db.collection(FIRESTORE_KB_COLLECTION).document(id)
        doc = ref.get()

        # Check if document exists and is not deleted
        if not doc.exists or doc.get("isDeleted"):
            raise HTTPException(status_code=404, detail="Not found ")

        update_dict = request_data.model_dump(exclude_unset=True)

        if not update_dict:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        ref.update(dict({"updatedAt": firestore.SERVER_TIMESTAMP}, **update_dict))

        return {"data": fix_firestore_dates(ref.get().to_dict())}
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kb/{id}/add/files")
async def add_files_kb(
    id: str,
    user_data: Annotated[dict, Depends(validate_usr)],
    files: List[UploadFile] = File(...),
):
    try:
        ref = db.collection(FIRESTORE_KB_COLLECTION).document(id)
        doc = ref.get()

        # Check if document exists
        if not doc.exists or doc.get("isDeleted"):
            raise HTTPException(status_code=404, detail="Not found")

        files_data, file_ids = await upload_files(user_data, id, files)

        current_list = doc.get("filesIds")
        if current_list is None:
            current_list = []

        request_data_genai = [
            (
                {
                    "payload": [{
                        "kb_id": id,
                        "file_id": e["id"],
                        "gcs_uri": e["gcsPath"],
                        "name": e["name"],
                    }],
                    "endpoint": "upload-files",
                }
            )
            for e in files_data
        ]
        logger.info(f"[add_files_kb] - Send request to genai to update. Data: {request_data_genai}")
        embedding_results = {}
        result_proxy = await send_request_genai_sandbox_array(request_data_genai)
        final_list_ids = []
        # Check results, if they are sucessful dont do anything, else delete the firestore records and gcs records
        for result in result_proxy:
            response = result.get("response")
            payload: dict = result.get("request_payload")[0]
            file_name = payload.get("name")
            file_id = payload.get("file_id")
            gcs_path = payload.get("gcs_uri")
            json_response = result.get("json_response")
            if not response.status == 200:
                logger.warning(
                    f"[add_files_kb] - Send request to genai to update result in status: {response.status}. json-body: {json_response}"
                )
                embedding_results = {f"{file_name}": "failed", **embedding_results}
                db.collection(FIRESTORE_FILES_COLLECTION).document(file_id).delete()
                prefix = gcs_path.replace(f"gs://{bucket.name}/", "")
                blobs = bucket.list_blobs(prefix=prefix)
                for blob in blobs:
                    blob.delete()
            else:
                logger.info(
                    f"[add_files_kb] - Send request to genai to update result in status: {response.status}. json-body: {json_response}"
                )
                embedding_results = {f"{file_name}": "success", **embedding_results}
                final_list_ids.append(file_id)
        new_list = list(set(final_list_ids) | set(current_list))
        ref.update({"filesIds": new_list})

        return {
            "data": fix_firestore_dates(ref.get().to_dict()),
            "embedding_results": embedding_results,
        }
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kb/{id}/remove/files")
async def remove_files_kb(id: str, request_data: KnowledgeBaseRemoveFilesRequest):
    try:
        file_ids_removed = request_data.file_ids
        ref = db.collection(FIRESTORE_KB_COLLECTION).document(id)
        doc = ref.get()

        # Check if document exists
        if not doc.exists or doc.get("isDeleted"):
            raise HTTPException(status_code=404, detail="Not found")

        for file_id_to_remove in file_ids_removed:
            if not file_id_to_remove in doc.get("filesIds"):
                raise HTTPException(
                    status_code=400, detail=f"Invalid file_id: {file_id_to_remove}"
                )

        files_ref = db.collection(FIRESTORE_FILES_COLLECTION).where("__name__", "in", file_ids_removed)

        files_result = files_ref.get()
        request_data_genai = [
            (
                {
                    "payload": [{
                        "kb_id": id,
                        "file_id": e.get("id"),
                        "gcs_uri": e.get("gcsPath"),
                    }],
                    "endpoint": "/delete-files",
                }
            )
            for e in files_result
        ]

        logger.info(f"[remove_files_kb] - Send request to genai to update. Data: {request_data_genai}")

        result_proxy = await send_request_genai_sandbox_array(request_data_genai)

        final_to_delete: List[firestore.DocumentSnapshot] = []
        final_ids_remove: List[str] = []
        embedding_results = {}
        # Check results, if they are sucessful add them to the array to delete them from gcs and firestore, else dont do anything
        for result in result_proxy:
            response = result.get("response")
            payload: dict = result.get("request_payload")[0]
            file_id = payload.get("file_id")
            json_response = result.get("json_response")
            if not response.status == 200:
                logger.warning(response.status)
                embedding_results = {f"{file_id}": "failed", **embedding_results}
                logger.warning(
                    f"[remove_files_kb] - Send request to genai to update result in status: {response.status}. json-body: {json_response}"
                )
            else:
                embedding_results = {f"{file_id}": "success", **embedding_results}
                final_ids_remove.append(file_id)
                find = [x for x in files_result if x.id == file_id]
                if find:
                    final_to_delete.append(find[0])
                    logger.info(
                        f"[remove_files_kb] - Send request to genai to update result in status: {response.status}. json-body: {json_response}"
                    )

        # Delete GCS PATHS
        for file in final_to_delete:
            prefix = file.get("gcsPath").replace(f"gs://{bucket.name}/", "")
            blobs = bucket.list_blobs(prefix=prefix)
            for blob in blobs:
                blob.delete()

        # Delete in firestore
        batch = db.batch()
        for file in final_to_delete:
            batch.delete(file.reference)
        batch.commit()

        # Update firestore
        current_list = doc.get("filesIds")
        if current_list is None:
            current_list = []

        new_list = list(set(current_list) - set(final_ids_remove))
        ref.update({"filesIds": new_list})

        return {
            "data": fix_firestore_dates(ref.get().to_dict()),
            "embedding_results": embedding_results,
        }

    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/kb/{id}")
async def delete_kb(id: str):
    try:
        ref = db.collection(FIRESTORE_KB_COLLECTION).document(id)
        doc = ref.get()

        # Check if document exists
        if not doc.exists or doc.get("isDeleted") or doc.get("type") == "chat-default":
            raise HTTPException(status_code=404, detail="Not found")

        ref.update({"isDeleted": True})

        return {"data": True}

    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kb/listing/predefined", response_model=BasicListResponse)
async def get_kbs(
    cursor: Optional[str] = Query(None, description="Document ID to start after"),
    limit: int = Query(50, description="Number of results to return"),
    order_by: Optional[str] = Query(None, description="name:asc, name:desc"),
    filters: Optional[List[str]] = Query(
        None, description="Filters to apply, e.g., name:==:chat, name:>=:chat"
    ),
):
    ref = (
        db.collection(FIRESTORE_KB_COLLECTION)
        .where("isDeleted", "==", False)
        .where("type", "==", "predefined")
        .order_by("updatedAt", "DESCENDING")
        .order_by("name", "ASCENDING")
        .limit(limit)
    )
    ref = apply_filters(ref, filters, ["isDeleted", "createdById", "type"])
    ref = apply_orders_by(ref, order_by)
    final_ref = apply_cursor(ref, FIRESTORE_KB_COLLECTION, cursor)
    records = final_ref.get()
    return {"data": [fix_firestore_dates(e.to_dict()) for e in records]}


@router.get("/kb/listing/user/public", response_model=BasicListResponse)
async def get_kbs(
    user_data: Annotated[
        dict,
        Depends(validate_usr),
    ],
    cursor: Optional[str] = Query(None, description="Document ID to start after"),
    limit: int = Query(50, description="Number of results to return"),
    order_by: Optional[str] = Query(None, description="name:desc, name:asc"),
    filters: Optional[List[str]] = Query(
        None, description="Filters to apply, e.g., name:==:chat, name:>=:chat"
    ),
):
    ref = (
        db.collection(FIRESTORE_KB_COLLECTION)
        .where("isDeleted", "==", False)
        .where("public", "==", True)
        .where("createdById", "!=", user_data["user_id"])
        .order_by("updatedAt", "DESCENDING")
        .order_by("name", "ASCENDING")
        .limit(limit)
    )
    ref = apply_filters(ref, filters, ["isDeleted", "createdById", "public"])
    ref = apply_orders_by(ref, order_by)
    final_ref = apply_cursor(ref, FIRESTORE_KB_COLLECTION, cursor)
    records = final_ref.get()
    return {"data": [fix_firestore_dates(e.to_dict()) for e in records]}


@router.get("/kb/listing/user/private", response_model=BasicListResponse)
async def get_kbs(
    user_data: Annotated[
        dict,
        Depends(validate_usr),
    ],
    cursor: Optional[str] = Query(None, description="Document ID to start after"),
    limit: int = Query(50, description="Number of results to return"),
    order_by: Optional[str] = Query(None, description="name:desc, name:asc"),
    filters: Optional[List[str]] = Query(
        None, description="Filters to apply, e.g., name:==:chat, name:>=:chat"
    ),
):
    ref = (
        db.collection(FIRESTORE_KB_COLLECTION)
        .where("isDeleted", "==", False)
        .where("createdById", "==", user_data["user_id"])
        .order_by("updatedAt", "DESCENDING")
        .order_by("name", "ASCENDING")
        .limit(limit)
    )
    ref = apply_filters(ref, filters, ["isDeleted", "createdById"])
    ref = apply_orders_by(ref, order_by)
    final_ref = apply_cursor(ref, FIRESTORE_KB_COLLECTION, cursor)
    records = final_ref.get()
    return {"data": [fix_firestore_dates(e.to_dict()) for e in records]}
