import os
from concurrent.futures import ThreadPoolExecutor, as_completed 
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from itertools import chain


from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import BaseNode, Document, TextNode
from llama_index.core.node_parser import SentenceSplitter
from vertexai.preview.language_models import TextEmbeddingInput, TextEmbeddingModel

from pinecone import Pinecone, Index

from gcsfs import GCSFileSystem
from google.cloud import storage, aiplatform

from fastapi import FastAPI

from log import get_logger, CloudLogger
import constants as c 
import models

logger = get_logger(name=c.LOGGER_NAME, project=c.PROJECT_NAME)
app = FastAPI()

def get_doc_lookup(docs: list[Document]) -> dict[str, list[Document]]:
    lookup = {}
    for doc in docs:
        uri = doc.metadata['file_path']
        if lookup.get(uri):
            lookup[uri].append(doc)
        else:
            lookup[uri] = [doc]
    return lookup

def get_custom_metadata(
    gcs_client: storage.Client,
    doc_lookup: dict[str, list[Document]]
) -> dict[str, dict]:

    lookup = {}
    for uri, docs in doc_lookup.items():
        bucket_name = uri.split('/')[0]
        bucket = gcs_client.get_bucket(bucket_name)

        prefix = '/'.join(uri.split('/')[1:])
        blob = bucket.get_blob(prefix)
        blob.reload()
        metadata = blob.metadata
        lookup[uri] = {
            'documents': docs,
            'metadata': metadata
        }
    return lookup

def get_gcs_metadata(
    gcs_client: storage.Client,
    uris: list[str]
) -> dict[str, dict]:
    metadata = {}
    bucket_name = uris[0].split('/')[0]
    bucket = gcs_client.get_bucket(bucket_name)
    for uri in uris:
        if uri.split('/')[0] != bucket_name:
            bucket_name = uri.split('/')[0]
            bucket = gcs_client.get_bucket(bucket_name)

        prefix = '/'.join(uri.split('/')[1:])
        blob = bucket.get_blob(prefix)
        blob.reload()
        metadata[uri] = blob.metadata
        metadata[uri]['blob'] = blob

        if uri.split('/')[2] == 'image_descriptions':
            metadata[uri]['id'] = f'{metadata[uri]["id"]}_{uri.split("/")[-1].split(".")[0]}'

    return metadata


def _node_parser(documents: list[Document]) -> list[BaseNode]:
    node_parser = SentenceSplitter(
        chunk_size=256,
        chunk_overlap=20
    )
    nodes = node_parser.get_nodes_from_documents(documents, show_progress=True)
    nodes = [node for node in nodes if node.text.strip()]
    return nodes

def get_nodes(
    doc_lookup: dict[str, dict],
) -> dict[str, dict]:
    for uri, data in doc_lookup.items():
        docs = data['documents']
        nodes = _node_parser(docs)
        data['nodes'] = nodes
    return doc_lookup

def embed_text_batch(
    texts: list[str],
    task: str = "RETRIEVAL_DOCUMENT",
    model_name: str = "text-embedding-004",
    dimensionality: int = 768,
) -> list[list[float]]:
    model = TextEmbeddingModel.from_pretrained(model_name)
    inputs = [TextEmbeddingInput(text, task) for text in texts]
    kwargs = dict(output_dimensionality=dimensionality) if dimensionality else {}
    embeddings = model.get_embeddings(inputs, **kwargs)
    return [embedding.values for embedding in embeddings]


def embed_nodes(
    nodes: list[BaseNode],
    model: TextEmbeddingModel,
    task: str = "RETRIEVAL_DOCUMENT",
    dimensionality: int = 768,
) -> list[BaseNode]:
    
    texts = [node.text for node in nodes]
    inputs = [TextEmbeddingInput(text, task) for text in texts]
    kwargs = dict(output_dimensionality=dimensionality) if dimensionality else {}
    embeddings = model.get_embeddings(inputs, **kwargs)
    embeddings = [e.values for e in embeddings]

    for node, embedding in zip(nodes, embeddings):
        node.embedding = embedding
        
    return nodes

def embed_empty_node(
    model: TextEmbeddingModel,
    dimensionality: int = 768,
    task: str = "RETRIEVAL_DOCUMENT",
) -> TextNode:
    node = TextNode()
    node.text = ' '
    texts = [node.text]
    inputs = [TextEmbeddingInput(text, task) for text in texts]
    kwargs = dict(output_dimensionality=dimensionality) if dimensionality else {}
    embeddings = model.get_embeddings(inputs, **kwargs)
    embeddings = [e.values for e in embeddings]
    node.embedding = embeddings[0]
    return node

    
def generate_embeddings(
    doc_lookup: dict[str, dict],
    model: TextEmbeddingModel,
    batch_size: int = 32
):
    all_nodes = []
    for uri, data in doc_lookup.items():
        nodes = data['nodes']
        all_nodes.extend(nodes)

    node_batches = [all_nodes[i : i + batch_size] for i in range(0, len(all_nodes), batch_size)]

    all_embedded_nodes = []
    for i, node_batch in enumerate(node_batches):
        print(f'Embedding batch {i+1}/{len(node_batches)}')

        embedded_nodes = embed_nodes(node_batch, model)
        all_embedded_nodes.extend(embedded_nodes)

    return doc_lookup


def upsert_vectors(
    doc_lookup: dict[str, dict],
    index: Index,
    id_prefix: str,
    model: TextEmbeddingModel
):
    records = []
    for uri, data in doc_lookup.items():       
        id = data['metadata']['id']
        folder_prefix = uri.split('/')[2]

        metadata = {
            'kb_id': id_prefix,
            'uri': uri,
            'gcs_file_extension': uri.split('/')[-1].split('.')[-1],
            'drive_createdTime': data['metadata']['createdTime'],
            'drive_modifiedTime': data['metadata']['modifiedTime'],
            'drive_id': data['metadata']['id'],
            'drive_name': data['metadata']['name'],
            'drive_webViewLink': data['metadata']['webViewLink'],
            'drive_mimeType': data['metadata']['mimeType'],
        }

        if folder_prefix == 'image_descriptions':
            metadata['image_description'] = True
            id += '_' + uri.split('/')[-1].split('.')[0]
        elif folder_prefix == 'docx_to_pdf':
            metadata['docx_to_pdf'] = True


        if data['nodes']:
            for i,node in enumerate(data['nodes']):
                metadata.update({'text': node.text})
                record = {
                    'id': f'{id_prefix}##{id}##{i}',
                    'values': node.embedding,
                    'metadata': metadata
                }
                records.append(record)

        else:  # when file has no text (e.g. PDF with only images)
            node = embed_empty_node(model)
            metadata.update({'text': node.text})
            record = {
                'id': f'{id_prefix}##{id}##0',
                'values': node.embedding,
                'metadata': metadata
            }
            records.append(record)

    batch_size = 100
    record_batches = [records[i : i + batch_size] for i in range(0, len(records), batch_size)]
    for i, batch in enumerate(record_batches):
        print(f'Upserting batch {i+1}/{len(record_batches)}')
        response = index.upsert(batch)
        print(response)
    

def get_ids_with_prefix(
    index: Index,
    id_prefix: str,
) -> list[str]: 
    ids = []
    for id_batch in index.list(prefix=id_prefix):
        ids.extend(id_batch)
    return ids

def get_directives(
    index: Index,
    gcs_meta: dict[str, dict],
    id_prefix: str,
):
    pc_ids = get_ids_with_prefix(index, id_prefix)
    pc_file_ids = set([pc_id.split('##')[1] for pc_id in pc_ids])
    gcs_file_ids = [meta['id'] for meta in gcs_meta.values()]

    # ids present in pinecone that are not present in GCS
    deletes = [pc_id for pc_id in pc_ids if pc_id.split('##')[1] not in gcs_file_ids] 

    # get URIs in GCS that are not in pinecone
    inserts = [uri for uri, meta in gcs_meta.items() if meta['id'] not in pc_file_ids]

    # files to check for updates:
    ids_to_fetch = []
    for uri, meta in gcs_meta.items():
        file_id = meta['id']
        if file_id in pc_file_ids:
            matching_pc_ids = [pc_id for pc_id in pc_ids if pc_id.split('##')[1] == file_id]
            ids_to_fetch.append(matching_pc_ids[0])
         

    if ids_to_fetch:
        id_batches = [ids_to_fetch[i : i + 100] for i in range(0, len(ids_to_fetch), 100)]
        records_to_check = {}
        for batch in id_batches:
            records = index.fetch(ids=batch).to_dict()['vectors']
            records_to_check.update(records)
        for vec_id, vector in records_to_check.items():
            vec_meta = vector['metadata']

            strfmt = '%Y-%m-%dT%H:%M:%S.%fZ'
            rcd_modified_time = vec_meta['drive_modifiedTime']
            rcd_modified_time = datetime.strptime(rcd_modified_time, strfmt)
            
            uri = vec_meta['uri']
            gcs_modified_time = gcs_meta[uri]['modifiedTime']
            gcs_modified_time = datetime.strptime(gcs_modified_time, strfmt)

            if rcd_modified_time < gcs_modified_time:
                if uri not in inserts:
                    inserts.append(uri)

                delete_prefix = '##'.join(vec_id.split('##')[:-1])
                ids_to_delete = [id for id in pc_ids if id.startswith(delete_prefix)]
                deletes.extend(ids_to_delete)

    else:
        print('No records to check for updates')

    return {
        'deletes': deletes,
        'inserts': inserts
    }

def list_supported_files(
    fs: GCSFileSystem,
    bucket: str,
    folder_id: str
) -> list[str]: 
    docx_to_pdf = fs.glob(f'{bucket}/{folder_id}/docx_to_pdf/*.pdf')
    
    image_descriptions = fs.glob(f'{bucket}/{folder_id}/image_descriptions/**/*.txt')
    image_descriptions = [uri for uri in image_descriptions if uri.split('/')[-1] != 'placeholder.txt']

    raw = fs.glob(f'{bucket}/{folder_id}/raw/*')
    supported_extensions = ['csv', 'pdf', 'txt']
    raw_supported = [uri for uri in raw if uri.split('/')[-1].split('.')[-1] in supported_extensions]
    
    raw_unsupported = [uri for uri in raw if uri not in raw_supported]
    # exclude docx from unsupported as these are converted to pdf
    raw_unsupported = [uri for uri in raw_unsupported if uri.split('/')[-1].split('.')[-1] != 'docx']

    logger.log_struct(
        message=f'Found {len(raw_unsupported)} files with unsupported filetypes. These files will not be processed.',
        unsupported_files=raw_unsupported,
        severity='WARNING'
    )

    all_files = list(chain(docx_to_pdf, image_descriptions, raw_supported))
    return all_files

def load_files(
    files: list[str],
    fs: GCSFileSystem,
    gcs: storage.Client,
    folder_id: str,
    index: Index
):
    reader = SimpleDirectoryReader(
        input_files=files,
        fs=fs,
    )

    docs: list[Document] = reader.load_data()

    doc_lookup = get_doc_lookup(docs)
    doc_lookup = get_custom_metadata(gcs, doc_lookup)
    doc_lookup = get_nodes(doc_lookup)

    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    doc_lookup = generate_embeddings(
        doc_lookup,
        model=model
    )

    id_prefix = f'kb-drive-{folder_id}'
    upsert_vectors(doc_lookup, index, id_prefix=id_prefix, model=model)


    pass
    

def init_clients(project: str) -> tuple[GCSFileSystem, storage.Client, Pinecone]:
    
    required_env_variables = [
        'PINECONE_API_KEY',
        'GCP_REGION',
    ]
    for var in required_env_variables:
        if not os.getenv(var):
            msg = f'{var} not found in environment variables. Required environment variables: {required_env_variables}'
            logger.error(msg)
            raise Exception(msg)
        
    creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if creds:
        fs = GCSFileSystem(
            project=project,
            token=creds
        )
    else:
        fs = GCSFileSystem(project=project)

    gcs = storage.Client(project=project)
    aiplatform.init(project=project, location=os.getenv('GCP_REGION'))
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    
    return fs, gcs, pc


def _main(
    project: str,
    bucket: str,
    folder_id: str,
    index_name: str,
    batch_size: int,
):
    fs, gcs, pc = init_clients(project)
    index = pc.Index(index_name)

    all_files = list_supported_files(fs, bucket, folder_id)

    logger.info(f'Getting GCS metadata...')
    gcs_meta = get_gcs_metadata(gcs, all_files)

    logger.info(f'Getting directives...')
    directives = get_directives(
        index=index,
        gcs_meta=gcs_meta,
        id_prefix=f'kb-drive-{folder_id}'
    )
 
    if directives['deletes']:
        logger.info(f'Deleting {len(directives["deletes"])} records from Pinecone')
        batch_size = 1000
        batches = [directives['deletes'][i : i + batch_size] for i in range(0, len(directives['deletes']), batch_size)]
        for batch in batches:
            index.delete(ids=batch)
    else:
        logger.info('No records to delete')

    if directives['inserts']:
        files = directives['inserts']
        logger.info(f'Found {len(files)} total files to load')
    else:
        logger.info('No new files to insert. Exiting...')
        return {'result': 'DONE'}
    
    batch_size = batch_size if len(files) > batch_size else len(files)
    batch = files[:batch_size]
    logger.log_struct(
        message=f'Loading {len(batch)} files...',
        files=batch
    )
    load_files(
        files=batch,
        fs=fs,
        gcs=gcs,
        folder_id=folder_id,
        index=index
    )
    logger.info('Done loading files')
    return {'result': 'CONTINUE'}


@app.post('/load-drive-files')
def main(req: models.LoadDriveFilesRequest):
    try:
        return _main(
            project=req.project,
            bucket=req.bucket,
            folder_id=req.folder_id,
            index_name=req.index_name,
            batch_size=req.batch_size
        )
    except Exception as e:
        logger.error(e)
        return {'error': str(e)}


if __name__ == '__main__':
    # set GOOGLE_APPLICATION_CREDENTIALS if running locally

    PROJECT = 'bd-genai-internal'
    BUCKET = 'bd-drive-data'
    FOLDER = '11wtvASfuHoLKkLr_Z_rj85BXgu80MR_V'
    INDEX_NAME = 'genai-sandbox'
    BATCH_SIZE = 100
    _main(
        project=PROJECT,
        bucket=BUCKET,
        folder_id=FOLDER,
        index_name=INDEX_NAME,
        batch_size=BATCH_SIZE
    )

    pass
