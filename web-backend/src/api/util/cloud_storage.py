import logging
import datetime
from google.cloud import storage

import google.auth
import google.auth.transport.requests


logger = logging.getLogger(__name__)


# https://cloud.google.com/storage/docs/samples/storage-generate-signed-url-v4
def generate_download_signed_url(bucket_name, blob_name):
    logger.info(f"Generating signed URL for {bucket_name}/{blob_name}")
    credentials = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])[0]

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    expiration = datetime.timedelta(hours=12)

    # Perform a refresh request to get the access token of the current credentials (Else, it's None)
    r = google.auth.transport.requests.Request()
    credentials.refresh(r)

    # If you use a service account credential, you can use the embedded email
    service_account_email = credentials.service_account_email
    access_token = credentials.token

    url = blob.generate_signed_url(expiration=expiration,service_account_email=service_account_email, access_token=access_token)
    logger.info(f"Generated GET signed URL")
    return url