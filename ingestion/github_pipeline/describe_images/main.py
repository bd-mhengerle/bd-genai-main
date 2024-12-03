import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta

import requests
from gcsfs import GCSFileSystem
from google.cloud import storage, firestore
import google.auth.transport.requests
from google.oauth2 import id_token

from flask.wrappers import Request

from log import get_logger, CloudLogger
import constants as c


logger: CloudLogger = get_logger(c.LOGGER_NAME, c.PROJECT_ID)

@dataclass
class ImageDescriptionRequest:
    source_uri: str
    target_folder_uri: str
    

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
    reqs: list[ImageDescriptionRequest]
):
    
    headers = get_headers()

    reqs = [asdict(req) for req in reqs]
    res = requests.post(
        url=f'{c.IMAGE_DESCRIPTION_SERVICE_URL}/describe-images',
        headers=headers,
        json=reqs
    )
    return res

def _get_metadata_from_gcs(
    gcs: storage.Client,
    uris: list[str]
):
    metadata = {}
    bucket_name = uris[0].split('/')[0]
    bucket = gcs.get_bucket(bucket_name)
    for uri in uris:
        if uri.split('/')[0] != bucket_name:
            bucket_name = uri.split('/')[0]
            bucket = gcs.get_bucket(bucket_name)
        prefix = '/'.join(uri.split('/')[1:])
        blob = bucket.get_blob(prefix)
        blob.reload()
        metadata[uri] = blob.metadata

    return metadata
    
def _get_metadata_from_cache(
    fs_db: firestore.Client,
    collection_name: str,
    bucket_name: str,
    freshness_minutes: int
):
    coll = fs_db.collection(collection_name)
    query = coll.where('job_id', '==', c.FS_JOB_ID)\
                .where('bucket', '==', bucket_name)
    doc = list(query.stream())[0]
    doc_dict = doc.to_dict()

    updated_ts = doc_dict['last_updated_ts']

    updated_ts = datetime.fromisoformat(updated_ts)
    utc_now = datetime.now(tz=timezone.utc)

    if (utc_now - updated_ts) > timedelta(minutes=freshness_minutes):
        return None
    else:
        return doc_dict['metadata']


def get_pdf_metadata(
    gcs: storage.Client,
    fs_db: firestore.Client,
    collection_name: str,
    bucket_name: str,
    uris: list[str],
    freshness_minutes: int
):
    metadata = _get_metadata_from_cache(
        fs_db=fs_db,
        collection_name=collection_name,
        bucket_name=bucket_name,
        freshness_minutes=freshness_minutes
    )
    if metadata is None:
        logger.info(f'Unable to fetch metadata from cache with freshness of {freshness_minutes} minutes. Fetching from GCS.')
        metadata = _get_metadata_from_gcs(
            gcs=gcs,
            uris=uris
        )

        # update cache
        coll_ref = fs_db.collection(collection_name)
        doc = list(coll_ref.where('bucket', '==', bucket_name).stream())[0]
        doc_ref = coll_ref.document(doc.id)
        data = {
            'job_id': c.FS_JOB_ID,
            'bucket': bucket_name,
            'metadata': metadata,
            'last_updated_ts': datetime.now(tz=timezone.utc).isoformat()
        }
        doc_ref.set(data, merge=False)

    return metadata

def get_description_meta(
    gcs: storage.Client,
    fs: GCSFileSystem,
    bucket: str
):
    bkt = gcs.get_bucket(bucket)
    folders = fs.glob(f'{bucket}/descriptions/**/*.pdf')
    meta = {}
    for folder in folders:
        first_file = fs.glob(f'{folder}/*')[0]
        file_prefix = '/'.join(first_file.split('/')[1:])
        blob = bkt.blob(file_prefix)
        blob.reload()
        meta['/'.join(folder.split('/')[2:])] = {
            'folder_uri': folder,
            'latest_commit_ts': blob.metadata['latest_commit_ts']
        }
    return meta

def get_directives(
    pdf_meta: dict,
    desc_meta: dict,
    bucket: str
):
    directives = {}
    # get descriptions to delete
    for prefix, meta in desc_meta.items():
        if prefix not in pdf_meta:
            directives[f'{bucket}/descriptions/{prefix}'] = 'delete'
    
    # get pdfs to process
    for prefix, meta in pdf_meta.items():
        if prefix not in desc_meta:  # insert
            directives[f'{bucket}/pdf/{prefix}'] = 'process'
        else:  # update
            strf = '%Y-%m-%d %H:%M:%S'
            pdf_commit_ts = datetime.strptime(meta['latest_commit_ts'], strf)
            desc_commit_ts = datetime.strptime(desc_meta[prefix]['latest_commit_ts'], strf)
            if pdf_commit_ts > desc_commit_ts:
                directives[f'{bucket}/pdf/{prefix}'] = 'process'
    
    return directives

def _get_txt_uris(
    fs: GCSFileSystem,
    bucket: str
) -> list[str]:
    """Only get first image description URI for each PDF."""
    txt_uris = fs.glob(f'{bucket}/descriptions/**/*.txt')
    uri_dict = {}
    for uri in txt_uris:
        prefix = '/'.join(uri.split('/')[:-1])
        if prefix in uri_dict:
            continue
        uri_dict[prefix] = uri

    txt_uris = list(uri_dict.values())

    return txt_uris

    

def _main(
    bucket: str,
    batch_size: int,
    cache_freshness: int
):
    gcs = storage.Client(project=c.PROJECT_ID)
    fs = GCSFileSystem(project=c.PROJECT_ID)
    fstore = firestore.Client(project=c.PROJECT_ID, database=c.FS_DATABASE)

    pdf_uris = fs.glob(f'{bucket}/pdf/**/*.pdf')

    pdf_meta = get_pdf_metadata(
        gcs=gcs,
        fs_db=fstore,
        collection_name=c.FS_COLLECTION_NAME,
        bucket_name=bucket,
        uris=pdf_uris,
        freshness_minutes=cache_freshness
    )
    pdf_meta = {
        '/'.join(k.split('/')[2:]):v for k,v in pdf_meta.items() if k in pdf_uris
    }
    desc_meta = get_description_meta(
        gcs=gcs,
        fs=fs,
        bucket=bucket
    ) 

    directives = get_directives(
        pdf_meta=pdf_meta,
        desc_meta=desc_meta,
        bucket=bucket
    )
    to_delete = [
        folder_prefix for folder_prefix, action in directives.items() if action == 'delete'
    ]
    if to_delete:
        logger.log_struct(
            message=f'Deleting {len(to_delete)} image_description folders...',
            folders=to_delete
        )
        for folder_prefix in to_delete:
            fs.rm(folder_prefix, recursive=True)

    to_process = [
        pdf_prefix for pdf_prefix, action in directives.items() if action == 'process'
    ]
    logger.info(f'Files remaining to process: {len(to_process)}')
    if not to_process:
        logger.info('No files to process.')
        return {'result': 'DONE'}
    
    batch_size = batch_size if len(to_process) > batch_size else len(to_process)
    reqs = []
    for prefix in to_process[:batch_size]:
        pdf_uri = prefix
        folder_uri = f'{bucket}/descriptions/{"/".join(prefix.split("/")[2:])}'
        reqs.append(ImageDescriptionRequest(source_uri=pdf_uri, target_folder_uri=folder_uri))
    
    logger.log_struct(
        message=f'Calling image description service with {len(reqs)} requests...',
        requests=[asdict(req) for req in reqs]
    )
    res = call_service(reqs)
    elapsed = res.elapsed.total_seconds()
    logger.info(f'Image description service call completed in {elapsed} seconds.')

    return {'result': 'CONTINUE'}

def main(request: Request):
    data = json.loads(request.data.decode('utf-8'))

    bucket = data['bucket']
    batch_size = int(data['batch_size'])
    cache_freshness = int(data['cache_freshness'])

    result = _main(
        bucket=bucket,
        batch_size=batch_size,
        cache_freshness=cache_freshness
    )

    return result


if __name__ == '__main__': 
    # for running locally
    os.environ['LOCAL'] = 'True'
    BUCKET = 'bd-gh-data-spot-sdk'

    result = _main(bucket=BUCKET, batch_size=10, cache_freshness=100)
    pass
   