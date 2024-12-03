import subprocess
import os
from uuid import uuid4

from fastapi import FastAPI
from google.cloud import storage

from models import GCSConversionRequest
import constants as c 

app = FastAPI()


def convert_docx_to_pdf(docx_path, output_dir=None):
    # Ensure the output directory is specified
    if output_dir is None:
        output_dir = os.path.dirname(docx_path)
    
    # Construct the command to convert the .docx file to PDF using LibreOffice
    command = [
        'soffice',
        # '--headless',
        '--convert-to',
        'pdf',
        '--outdir',
        output_dir,
        docx_path
    ]
    
    # Execute the command
    subprocess.run(command, check=True)


def process_request(
    req: GCSConversionRequest,
    gcs: storage.Client
):
    source_bucket = req.source_uri.split('/')[0]
    source_file = gcs.get_bucket(source_bucket).blob('/'.join(req.source_uri.split('/')[1:]))
    source_file.reload()
    source_metadata = source_file.metadata or {}

    # download file to data directory
    file_id = str(uuid4())
    source_file.download_to_filename(f'/app/data/{file_id}.docx')

    # convert to pdf
    print('Running PDF conversion...')
    convert_docx_to_pdf(f'/app/data/{file_id}.docx', output_dir='/app/data')

    # write to gcs
    print('Uploading PDF to GCS...')
    destination_bucket = req.destination_uri.split('/')[0]
    destination_file = gcs.get_bucket(destination_bucket).blob('/'.join(req.destination_uri.split('/')[1:]))
    destination_file.metadata = source_metadata
    destination_file.upload_from_filename(f'/app/data/{file_id}.pdf')

    # remove files
    print('Cleaning up...')
    os.remove(f'/app/data/{file_id}.docx')
    os.remove(f'/app/data/{file_id}.pdf')

@app.post('/docx-to-pdf')
def docx_to_pdf(reqs: list[GCSConversionRequest]):

    gcs = storage.Client(project=c.PROJECT_ID)

    for i,req in enumerate(reqs):
        print(f'Processing request {i+1} of {len(reqs)}...')
        process_request(req, gcs)

    return 200