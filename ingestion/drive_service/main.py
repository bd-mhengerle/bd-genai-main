import io
from datetime import datetime
import json

from google.cloud import storage, secretmanager
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

import constants as c
from log import get_logger, CloudLogger


logger = get_logger(c.LOGGER_NAME, c.PROJECT_ID)

def get_credentials(
        principal: str,
        creds_file: None | str = None
) -> service_account.Credentials:
    scopes = ['https://www.googleapis.com/auth/drive']
    if creds_file:
        credentials = service_account.Credentials.from_service_account_file(
            creds_file, scopes=scopes
        )
    else:
        # get credentials from secret manager
        client = secretmanager.SecretManagerServiceClient()
        value = client.access_secret_version(name=c.SA_SECRET_NAME)
        creds_dict = json.loads(value.payload.data.decode('UTF-8'))
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=scopes
        )

    return credentials.with_subject(principal)


def list_files_in_folder(
    service,
    folder_id: str,
) -> list[dict]:
    query = f"'{folder_id}' in parents and trashed = false"
    files = []
    page_token = None

    while True:
        results = service.files().list(
            q=query,
            fields='nextPageToken, files(*)',
            pageToken=page_token
        ).execute()
        items = results.get('files', [])
        
        for item in items:
            files.append(item)
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                files.extend(list_files_in_folder(service, item['id']))
        
        page_token = results.get('nextPageToken')
        if not page_token:
            break
    
    return files

def download_file(service, file_id) -> io.BytesIO:
    request = service.files().get_media(fileId=file_id)
    file_io = io.BytesIO()
    downloader = MediaIoBaseDownload(file_io, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")
    file_io.seek(0)
    return file_io

def export_file(service, file_id, mime_type) -> io.BytesIO:

    request = service.files().export_media(
        fileId=file_id, mimeType=mime_type
    )
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        logger.info(f"Download {int(status.progress() * 100)}.")

    return file.getvalue()

def get_gcs_metadata(
    gcs_client: storage.Client,
    bucket_name: str,
    folder_id: str
):
    bucket = gcs_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=f'{folder_id}/raw')
    metadata = {}
    for blob in blobs:
        blob.reload()
        fname = blob.name
        meta = blob.metadata or {}
        if 'id' not in meta.keys():
            blob.delete()
        else:
            id = meta['id']
            metadata[id] = meta
            metadata[id]['blob_name'] = fname
    return metadata

def get_directives(
    gcs_metadata: dict,
    drive_metadata: dict
):
    directives = {}
    for file_id, meta in drive_metadata.items():
        if file_id not in gcs_metadata:
            directives[file_id] = 'upload' 
        else:
            strfmt = '%Y-%m-%dT%H:%M:%S.%fZ'
            gcs_modified_time = datetime.strptime(
                gcs_metadata[file_id]['modifiedTime'], strfmt
            )
            drive_modified_time = datetime.strptime(
                meta['modifiedTime'], strfmt
            )
            if drive_modified_time > gcs_modified_time:
                directives[file_id] = 'upload'

    for file_id in gcs_metadata.keys():
        if file_id not in drive_metadata:
            directives[file_id] = 'delete'    

    return directives
    
def upload_to_gcs(
        gcs_client: storage.Client,
        bucket_name: str,
        folder_id: str,
        file_metadata,
        file_io,
        file_extension
    ):

    meta_tags = {
        'createdTime': file_metadata['createdTime'],
        'modifiedTime': file_metadata['modifiedTime'],
        'id': file_metadata['id'],
        'name': file_metadata['name'],
        'mimeType': file_metadata['mimeType'],
        'webViewLink': file_metadata['webViewLink'],
    }
    bucket = gcs_client.bucket(bucket_name)
    blob_name = f"{folder_id}/raw/{file_metadata['id']}.{file_extension}"
    blob = bucket.blob(blob_name)
    blob.metadata = meta_tags
    if not isinstance(file_io, io.BytesIO):
        file_io = io.BytesIO(file_io)
    blob.upload_from_file(file_io, rewind=True)
    logger.info(f"File uploaded to gs://{bucket_name}/{blob_name}.")

def main(
    creds: service_account.Credentials,
    folder_id: str,
    bucket_name: str 
):
    
    gcs = storage.Client()
    service = build('drive', 'v3', credentials=creds)

    # all_files = list_files_in_folder(service, folder_id)
    all_files = list_files_in_folder(service, folder_id)
    drive_meta = {  # remove folders from drive metadata
        file['id']: file for file in all_files
        if file['mimeType'] != 'application/vnd.google-apps.folder'
    }

    logger.info(f'Getting GCS metadata for {folder_id}.')
    gcs_meta = get_gcs_metadata(
        gcs_client=gcs,
        bucket_name=bucket_name,
        folder_id=folder_id
    )
    logger.info(f'Found {len(gcs_meta)} files in GCS.')

    directives = get_directives(
        gcs_metadata=gcs_meta,
        drive_metadata=drive_meta
    )

    logger.log_struct(
        message='Directives for file sync',
        directives=directives
    )
    for file, directive in directives.items():
        if directive == 'upload':
            if drive_meta[file]['mimeType'] in (
                'application/vnd.google-apps.document',
            ):
                logger.info(f"Exporting {file} to PDF.")
                file_io = export_file(
                    service=service,
                    file_id=file,
                    mime_type='application/pdf'
                )
                upload_to_gcs(
                    gcs_client=gcs,
                    bucket_name=bucket_name,
                    file_metadata=drive_meta[file],
                    file_io=file_io,
                    file_extension='pdf',
                    folder_id=folder_id
                )
            else:
                file_io = download_file(service, file)
                upload_to_gcs(
                    gcs_client=gcs,
                    bucket_name=bucket_name,
                    file_metadata=drive_meta[file],
                    file_io=file_io,
                    file_extension=drive_meta[file]['fileExtension'],
                    folder_id=folder_id
                )
        elif directive == 'delete':
            print(f"Deleting {file} from GCS.")
            bucket = gcs.bucket(bucket_name)
            blob = bucket.blob(gcs_meta[file]['blob_name'])
            blob.delete()


if __name__ == '__main__':
    from argparse import ArgumentParser
    
    parser = ArgumentParser()
    parser.add_argument('--principal', type=str, required=True)
    parser.add_argument('--folder_id', type=str, required=True)
    parser.add_argument('--bucket', type=str, required=True)
    parser.add_argument('--creds_file', type=str, required=False)
    args = parser.parse_args()

    PRINCIPAL = args.principal
    FOLDER_ID = args.folder_id
    BUCKET = args.bucket
    SA_CREDS = args.creds_file


    # SA_CREDS = 'credentials.json'
    # FOLDER_ID = '11wtvASfuHoLKkLr_Z_rj85BXgu80MR_V'
    # BUCKET = 'test-drive-sync'
    # PRINCIPAL = 'svc_genai-concierge@bostondynamics.com'

    credentials = get_credentials(
        principal=PRINCIPAL,
        creds_file=SA_CREDS
    )
    main(credentials, FOLDER_ID, BUCKET)