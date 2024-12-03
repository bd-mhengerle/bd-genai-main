from itertools import chain
import pathlib
from datetime import datetime
import pytz
import json

from fastapi import FastAPI
from google.cloud import storage, bigquery
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image, GenerationResponse 
import vertexai.preview.generative_models as generative_models

import fitz 
from fitz import Document 

from log import get_logger, CloudLogger
import constants as c
import models


logger: CloudLogger = get_logger(c.LOGGER_NAME, c.PROJECT_ID)
app = FastAPI()

def clean_images_dir(
        images_dir: str = c.PDF_IMAGES_DIR
    ):
    images_dir = pathlib.Path(images_dir)
    for file in images_dir.iterdir():
        file.unlink()
  
def get_pdf_from_gcs(
        gcs_client: storage.Client,
        uri: str
) -> tuple[Document, dict]:
    bucket_name = uri.split('/')[0]
    blob_name = '/'.join(uri.split('/')[1:])
    bucket = gcs_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.reload()
    metadata = blob.metadata
    document = fitz.open(stream=blob.download_as_bytes(), filetype='pdf')
    return document, metadata

def get_blob_metadata(
    gcs_client: storage.Client,
    uri: str 
) -> dict:
    bucket_name = uri.split('/')[0]
    blob_name = '/'.join(uri.split('/')[1:])
    bucket = gcs_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.metadata

def extract_images_from_pdf(
        pdf: Document,
        output_dir: str = c.PDF_IMAGES_DIR
    ) -> list[str]:
    images = set(chain(*[page.get_images(full=True) for page in pdf]))
    xrefs = [img[0] for img in images]
    
    page_mapper = {}
    for i, page in enumerate(pdf):
        for xref in xrefs:
            if page.get_image_rects(xref):
                page_mapper[xref] = i
    
    image_paths = []
    for xref, page_idx in page_mapper.items():
        image = pdf.extract_image(xref)
        output_path = f'{output_dir}/pg_{page_idx + 1}_xref_{xref}.{image["ext"]}'
        with open(output_path, 'wb') as f:
            f.write(image['image'])
        image_paths.append(output_path)

    return image_paths

def describe_pdf(
    model: GenerativeModel,
    uri: str,
) -> GenerationResponse:
    prompt = '''
    You are a very professional document summarization specialist.
    Please summarize the given document.
    '''
    generation_config = {
        'max_output_tokens': 250,
        'temperature': 1,
        'top_p': 0.95
    }
    pdf_file = Part.from_uri(f'gs://{uri}', mime_type='application/pdf')
    response = model.generate_content(
        [pdf_file, prompt],
        generation_config=generation_config
    )
    return response

def describe_image(
    model: GenerativeModel,
    image_path: str,
) -> tuple[str, list]:
    
    image = Part.from_image(
        Image.load_from_file(image_path)
    )
    
    generation_config = {
        "max_output_tokens": 750,
        "temperature": 1,
        "top_p": 0.95,
    }
    safety_settings = {
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_NONE,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_NONE,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
    }
    responses = model.generate_content(
        [image, 'Describe this image'],
        generation_config=generation_config,
        safety_settings=safety_settings,
        stream=True
    )
    return responses 

def write_descriptions_to_gcs(
    gcs_client: storage.Client,
    target_uri: str,
    image_descriptions: list[GenerationResponse],
    metadata: dict
) -> None:
    
    bucket = gcs_client.get_bucket(target_uri.split('/')[0])
    blob = bucket.blob('/'.join(target_uri.split('/')[1:])) 
    blob.metadata = metadata

    s = '\n'.join([response.text for response in image_descriptions])
    blob.upload_from_string(s)


def write_placeholder_to_gcs(
    gcs_client: storage.Client,
    target_uri: str,
    metadata: dict
):
    bucket = gcs_client.get_bucket(target_uri.split('/')[0])
    blob = bucket.blob('/'.join(target_uri.split('/')[1:])) 
    blob.metadata = metadata
    blob.upload_from_string('')

def main(
    gcs_client: storage.Client,
    model: GenerativeModel,
    uri: str,
    target_folder_uri: str
):

    # clean target_folder_uri
    bucket_name = target_folder_uri.split('/')[0]
    bucket = gcs_client.get_bucket(bucket_name)
    blobs = list(bucket.list_blobs(prefix='/'.join(target_folder_uri.split('/')[1:])))
    if blobs:
        logger.log_struct(
            message=f'Deleting existing blobs in {target_folder_uri}...',
            blobs=[blob.name for blob in blobs]
        )
        for blob in blobs:
            blob.delete()
        
    clean_images_dir()
    pdf, metadata = get_pdf_from_gcs(
        gcs_client=gcs_client,
        uri=uri
    )    

    image_paths: list[str] = extract_images_from_pdf(pdf)
    if not image_paths:
        logger.info(f'No images found in PDF: {uri}')
        target_uri = f'{target_folder_uri}/placeholder.txt'
        write_placeholder_to_gcs(
            gcs_client=gcs_client,
            target_uri=target_uri,
            metadata=metadata
        )
        return
   
    for i,image_path in enumerate(image_paths):
        print(f'---- {image_path} ----')
        img_descriptions = describe_image(
            model=model,
            image_path=image_path
        )
        # write_descriptions_to_gcs
        target_uri = f'{target_folder_uri}/image_{i}.txt'
        write_descriptions_to_gcs(
            gcs_client=gcs_client,
            target_uri=target_uri,
            image_descriptions=img_descriptions,
            metadata=metadata
        )
        
    clean_images_dir()

def get_generative_model():
    vertexai.init(project=c.PROJECT_ID, location='us-central1')
    return GenerativeModel('gemini-1.5-flash-001')

@app.post('/describe-images')
def describe_images(reqs: list[models.ImageDescriptionRequest]):

    gcs_client = storage.Client(c.PROJECT_ID)
    model = get_generative_model()
        
    for i,req in enumerate(reqs):
        logger.info(f'Processing request {i+1} of {len(reqs)}...')
        main(
            gcs_client=gcs_client,
            model=model,
            uri=req.source_uri,
            target_folder_uri=req.target_folder_uri
        )
    return {'result': 'DONE'}


if __name__ == '__main__':
    
    gcs = storage.Client(c.PROJECT_ID)
    model = get_generative_model()

    reqs = [
        {
            'source_uri': 'test-drive-sync/11wtvASfuHoLKkLr_Z_rj85BXgu80MR_V/docx_to_pdf/1-GJcERPVvprRKT37ly_9PuxVY1D0D4YE.pdf',
            'target_folder_uri': 'test-drive-sync/11wtvASfuHoLKkLr_Z_rj85BXgu80MR_V/image_descriptions/1-GJcERPVvprRKT37ly_9PuxVY1D0D4YE'
        }
    ]

    for req in reqs:
        main(
            gcs_client=gcs,
            model=model,
            uri=req['source_uri'],
            target_folder_uri=req['target_folder_uri']
        )
    


