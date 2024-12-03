import os
import requests
from datetime import datetime
import json

from google.cloud import storage
from gcsfs import GCSFileSystem
import google.auth.transport.requests
from google.oauth2 import id_token

from flask.wrappers import Request

import constants as c 
from log import get_logger, CloudLogger

logger = get_logger(c.LOGGER_NAME, c.PROJECT_ID)


def get_headers():
    is_local = os.environ.get('LOCAL', False)
    if is_local:
        logger.info("Running locally, using default credentials.")
        creds, project = google.auth.default()
        auth_req = google.auth.transport.requests.Request()
        creds.refresh(auth_req)
        return {'Authorization': f'bearer {creds.id_token}'}
    else:
        logger.info("Running in cloud, using service account credentials.")
        auth_req = google.auth.transport.requests.Request()
        id_token_str = id_token.fetch_id_token(auth_req, c.DOCX_TO_PDF_SERVICE_URL)
        return {'Authorization': f'bearer {id_token_str}'}


def call_service(
    reqs: list[dict]
):
    headers = get_headers()
    res = requests.post(
        url=f'{c.DOCX_TO_PDF_SERVICE_URL}/docx-to-pdf',
        headers=headers,
        json=reqs
    )
    return res


def get_raw_metadata(
    fs: GCSFileSystem,
    gcs: storage.Client,
    bucket: str,
    folder_id: str
):
    bkt = gcs.get_bucket(bucket)
    blobs = bkt.list_blobs(prefix=f'{folder_id}/raw/')
    meta_raw = {}
    for blob in blobs:
        if blob.name.endswith('.docx'):
            blob.reload()
            meta = blob.metadata
            id = meta['id']
            meta_raw[id] = {
                'uri': f'{bucket}/{blob.name}',
                'modifiedTime': meta['modifiedTime']
            }
    return meta_raw


def get_processed_metadata(
    fs: GCSFileSystem,
    gcs: storage.Client,
    bucket: str,
    folder_id: str
):
    bkt = gcs.get_bucket(bucket)
    blobs = bkt.list_blobs(prefix=f'{folder_id}/docx_to_pdf/')
    meta_processed = {}
    for blob in blobs:
        if blob.name.endswith('.pdf'):
            blob.reload()
            meta = blob.metadata
            id = meta['id']
            meta_processed[id] = {
                'uri': f'{bucket}/{blob.name}',
                'modifiedTime': meta['modifiedTime']
            }    
    return meta_processed

def get_directives(
    meta_raw: dict,
    meta_processed: dict
):
    directives = {}

    # processed files to delete
    for id, meta in meta_processed.items():
        if id not in meta_raw:
            directives[id] = 'delete'

    # raw files to process
    for id, meta in meta_raw.items():

        if id in meta_processed:  # check if raw file is more recently modified
            strfmt = '%Y-%m-%dT%H:%M:%S.%fZ'
            raw_modified_time = datetime.strptime(
                meta['modifiedTime'], strfmt
            )
            processed_modified_time = datetime.strptime(
                meta_processed[id]['modifiedTime'], strfmt
            )
            if raw_modified_time > processed_modified_time:
                directives[id] = 'process'
 
        else:  # file not present in processed directory
            directives[id] = 'process'
    
    return directives
            
    

def _main(
    bucket: str,
    folder_id: str,
    batch_size: int
):
    # init clients
    fs = GCSFileSystem(project=c.PROJECT_ID)
    gcs = storage.Client(project=c.PROJECT_ID)

    # get all docx files in /raw
    meta_raw = get_raw_metadata(fs, gcs, bucket, folder_id)
    meta_processed = get_processed_metadata(fs, gcs, bucket, folder_id)
    directives = get_directives(meta_raw, meta_processed)

    to_delete = [
        meta_processed[id]['uri'] for id, action in directives.items()
        if action == 'delete'
    ]
    if to_delete:
        logger.info(f"Cleaning {len(to_delete)} files from processed folder...")
        for uri in to_delete:
            fs.rm(uri)

    to_process = [
        meta_raw[id]['uri'] for id, action in directives.items()
        if action == 'process'
    ]
    logger.info(f'Files remaining to process: {len(to_process)}')
    if not to_process:
        logger.info("No files to process.")
        return {'result': 'DONE'}
    
    batch_size = batch_size if len(to_process) > batch_size else len(to_process)
    reqs = []
    for uri in to_process[:batch_size]:
        
        destination_fname = uri.split('/')[-1].replace('.docx', '.pdf')
        destination_uri = f'{bucket}/{folder_id}/docx_to_pdf/{destination_fname}'

        reqs.append({
            'source_uri': uri,
            'destination_uri': destination_uri
        })
        
    # call the docx-to-pdf service
    logger.info(f'Calling docx-to-pdf service with {len(reqs)} files...')
    response = call_service(reqs)

    elapsed = response.elapsed.total_seconds()
    logger.info(f"Service call took {elapsed} seconds.")

    return {'result': 'CONTINUE'}

def main(request: Request):
    data = json.loads(request.data.decode('utf-8'))

    bucket = data['bucket']
    folder_id = data['folder_id']
    batch_size = int(data['batch_size'])

    result = _main(
        bucket=bucket,
        folder_id=folder_id,
        batch_size=batch_size
    )

    return result


if __name__ == '__main__':

    os.environ['LOCAL'] = 'True'

    BUCKET = 'bd-drive-data'
    FOLDER_ID = '11wtvASfuHoLKkLr_Z_rj85BXgu80MR_V'
    BATCH_SIZE = 100

    _main(
        bucket=BUCKET,
        folder_id=FOLDER_ID,
        batch_size=BATCH_SIZE
    )