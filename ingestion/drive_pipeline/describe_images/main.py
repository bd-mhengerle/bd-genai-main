import json
import os
from datetime import datetime 

import requests

from google.cloud import storage
from gcsfs import GCSFileSystem
import google.auth.transport.requests
from google.oauth2 import id_token

from flask.wrappers import Request

import constants as c
from log import get_logger, CloudLogger

logger: CloudLogger = get_logger(c.LOGGER_NAME, c.PROJECT_ID)

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
        id_token_str = id_token.fetch_id_token(auth_req, c.IMAGE_DESCRIPTION_SERVICE_URL)
        return {'Authorization': f'bearer {id_token_str}'}
    
def call_service(
    reqs: list[dict]
):
    headers = get_headers()
    res = requests.post(
        url=f'{c.IMAGE_DESCRIPTION_SERVICE_URL}/describe-images',
        headers=headers,
        json=reqs
    )
    return res

def get_pdf_meta(
    gcs: storage.Client,
    bucket: str,
    folder_id: str
) -> dict:
    bkt = gcs.get_bucket(bucket)
    
    all_blobs = bkt.list_blobs(prefix=f'{folder_id}')
    pdf_blobs = [blob for blob in all_blobs if blob.name.endswith('.pdf')]

    meta = {}
    for blob in pdf_blobs:
        blob.reload()
        meta[blob.metadata['id']] = {
            'uri': f'{bucket}/{blob.name}',
            'modifiedTime': blob.metadata['modifiedTime']
        }
    return meta


def get_description_meta(
    gcs: storage.Client,
    fs: GCSFileSystem,
    bucket: str,
    folder_id: str
) -> dict:
    bkt = gcs.get_bucket(bucket)
    folders = fs.glob(f'{bucket}/{folder_id}/image_descriptions/*')
    meta = {}
    for folder in folders:
        first_file = fs.glob(f'{folder}/*')[0]
        file_prefix = '/'.join(first_file.split('/')[1:])
        blob = bkt.blob(file_prefix)
        blob.reload()
        meta[blob.metadata['id']] = {
            'folder_uri': f'{bucket}/' + '/'.join(file_prefix.split('/')[:-1]),
            'modifiedTime': blob.metadata['modifiedTime']
        }
    return meta

def get_directives(
    pdf_meta: dict,
    desc_meta: dict
):
    directives = {}

    # descriptions to delete
    for id, meta in desc_meta.items():
        if id not in pdf_meta:
            directives[id] = 'delete'
    
    # pdfs to process
    for id, meta in pdf_meta.items():
        if id not in desc_meta:
            directives[id] = 'process'
        else:
            strfmt = '%Y-%m-%dT%H:%M:%S.%fZ'
            pdf_time = datetime.strptime(meta['modifiedTime'], strfmt)
            desc_time = datetime.strptime(desc_meta[id]['modifiedTime'], strfmt)
            if pdf_time > desc_time:
                directives[id] = 'process'

    return directives 
    



def _main(
    bucket: str,
    folder_id: str,
    batch_size: int
):
    gcs = storage.Client(project=c.PROJECT_ID)
    fs = GCSFileSystem(project=c.PROJECT_ID)

    pdf_meta = get_pdf_meta(gcs, bucket, folder_id)
    desc_meta = get_description_meta(gcs, fs, bucket, folder_id)
    directives = get_directives(pdf_meta, desc_meta)

    # main logic
    to_delete = [
        desc_meta[id]['folder_uri'] for id, action in directives.items()
        if action == 'delete'
    ]
    if to_delete:
        logger.info(f'Deleting {len(to_delete)} image_description folders...')
        for folder_uri in to_delete:
            fs.rm(folder_uri, recursive=True)

    to_process = [
        {'pdf_uri': pdf_meta[id]['uri'], 'file_id': id} for id, action in directives.items()
        if action == 'process'
    ]
    logger.info(f'Files remaining to process: {len(to_process)}')
    if not to_process:
        logger.info('No PDFs to process.')
        return {'result': 'DONE'}
    
    batch_size = batch_size if len(to_process) > batch_size else len(to_process)
    reqs = []
    for meta in to_process[:batch_size]:
        req = {
            'source_uri': meta['pdf_uri'],
            'target_folder_uri': f'{bucket}/{folder_id}/image_descriptions/{meta["file_id"]}'
        }
        reqs.append(req)

    # call image description service
    logger.log_struct(
        f'Calling image description service with {len(reqs)} requests...',
        requests=reqs
    )
    res = call_service(reqs)

    elapsed = res.elapsed.total_seconds()
    logger.info(f'Image description service call completed in {elapsed} seconds.')

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
    
    # for running locally
    BUCKET = 'bd-drive-data'
    FOLDER_ID = '11wtvASfuHoLKkLr_Z_rj85BXgu80MR_V'
    BATCH_SIZE = 100

    os.environ['LOCAL'] = 'True'

    _main(BUCKET, FOLDER_ID, BATCH_SIZE)
