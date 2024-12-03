import os
from datetime import datetime, timezone, timedelta

from gcsfs import GCSFileSystem
from google.cloud import storage, aiplatform, firestore
from fastapi import FastAPI

from pinecone import Pinecone, Index
from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import BaseNode, Document, TextNode
from llama_index.core.node_parser import SentenceSplitter
from vertexai.preview.language_models import TextEmbeddingModel, TextEmbeddingInput

import constants as c 
from log import get_logger, CloudLogger
from models import LoadPineconeRequest


logger: CloudLogger = get_logger(name=c.LOGGER_NAME, project=c.PROJECT_ID)
app = FastAPI()

def init_clients(project: str) -> tuple[GCSFileSystem, storage.Client, Pinecone, firestore.Client]:
    
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
    fs_db = firestore.Client(project=project, database=c.FS_DATABASE)
    
    return fs, gcs, pc, fs_db


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
    query = coll.where('bucket', '==', bucket_name)\
                .where('job_id', '==', c.FS_DOCUMENT_ID_FIELD)
    doc = list(query.stream())[0]
    doc_dict = doc.to_dict()

    updated_ts = doc_dict['last_updated_ts']

    updated_ts = datetime.fromisoformat(updated_ts)
    utc_now = datetime.now(tz=timezone.utc)

    if (utc_now - updated_ts) > timedelta(minutes=freshness_minutes):
        return None
    else:
        return doc_dict['metadata']


def get_metadata(
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
        doc = list(coll_ref.where('bucket', '==', bucket_name)\
            .where('job_id', '==', c.FS_DOCUMENT_ID_FIELD)\
            .stream())[0]
        doc_ref = coll_ref.document(doc.id)
        data = {
            'job_id': c.FS_DOCUMENT_ID_FIELD,
            'bucket': bucket_name,
            'metadata': metadata,
            'last_updated_ts': datetime.now(tz=timezone.utc).isoformat()
        }
        doc_ref.set(data, merge=False)

    return metadata

def list_uris(
    fs: GCSFileSystem,
    bucket: str,
) -> list[str]:
    uris_pdf = fs.glob(f'{bucket}/pdf/**/*.pdf')
    uris_desc = fs.glob(f'{bucket}/descriptions/**/*.txt')
    all_uris = uris_pdf + uris_desc
    supported_uris = [uri for uri in all_uris if not uri.endswith('placeholder.txt')]
    return supported_uris

def get_ids_with_prefix(
    index: Index,
    id_prefix: str
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
    pc_ids = get_ids_with_prefix(index=index, id_prefix=id_prefix)
    pc_file_ids = set([pc_id.split('##')[1] for pc_id in pc_ids])
    gcs_file_ids = list(gcs_meta.keys())

    # delete: IDs present in pinecone but not in GCS
    deletes = [pc_id for pc_id in pc_ids if pc_id.split('##')[1] not in gcs_file_ids]

    # insert: IDs present in GCS but not in pinecone
    inserts = [uri for uri in gcs_file_ids if uri not in pc_file_ids]

    # files present in pinecone, check if need to be updated
    ids_to_fetch = []
    for uri, meta in gcs_meta.items():
        if uri in pc_file_ids:
            matching_pc_ids = [pc_id for pc_id in pc_ids if pc_id.split('##')[1] == uri]
            ids_to_fetch.extend(matching_pc_ids)
    
    if ids_to_fetch:
        id_batches = [ids_to_fetch[i : i + 100] for i in range(0, len(ids_to_fetch), 100)]
        records_to_check = {}
        for batch in id_batches:
            records = index.fetch(ids=batch).to_dict()['vectors']
            records_to_check.update(records)
        for vec_id, vector in records_to_check.items():
            vec_meta = vector['metadata']
            uri = vec_meta.get('description_uri')
            if uri is None:
                uri = vec_meta['pdf_uri']

            strf = '%Y-%m-%d %H:%M:%S'
            vec_commit_ts = datetime.strptime(vec_meta['latest_commit_ts'], strf)
            gcs_commit_ts = datetime.strptime(gcs_meta[uri]['latest_commit_ts'], strf)

            if vec_commit_ts < gcs_commit_ts:                
                inserts.append(uri)
                delete_prefix = f'{id_prefix}##{uri}'
                ids_to_delete = [pc_id for pc_id in pc_ids if pc_id.startswith(delete_prefix)]
                deletes.extend(ids_to_delete)
            

    return {
        'deletes': list(set(deletes)),
        'inserts': list(set(inserts))
    }


def _get_doc_lookup(
    docs: list[Document]
) -> dict[str, list[Document]]:
    lookup = {}
    for doc in docs:
        uri = doc.metadata['file_path']
        if lookup.get(uri):
            lookup[uri].append(doc)
        else:
            lookup[uri] = [doc]
    return lookup

def _attach_gcs_metadata_to_doc_lookup(
    doc_lookup: dict[str, list[Document]],
    gcs_metadata: dict[str, dict]
) -> dict[str, dict]:
    _doc_lookup = {}
    for uri, doc_list in doc_lookup.items():
        _doc_lookup[uri] = {
            'documents': doc_list,
            'gcs_metadata': gcs_metadata[uri]
        }
    return _doc_lookup

def _node_parser(documents: list[Document]):
    node_parser = SentenceSplitter(
        chunk_size=1024,
        chunk_overlap=20
    )
    nodes = node_parser.get_nodes_from_documents(documents, show_progress=True)
    nodes = [node for node in nodes if node.text.strip()]
    return nodes

def _get_nodes(doc_lookup: dict[str, dict]):
    for uri, data in doc_lookup.items():
        docs = data['documents']
        nodes = _node_parser(docs)
        data['nodes'] = nodes
    return doc_lookup

def _embed_nodes(
    nodes: list[BaseNode],
    model: TextEmbeddingModel,
    task: str = "RETRIEVAL_DOCUMENT",
    dimensionality: int = 768
) -> list[BaseNode]:
    texts = [node.text for node in nodes]
    inputs = [TextEmbeddingInput(text, task) for text in texts]
    kwargs = dict(output_dimensionality=dimensionality) if dimensionality else {}
    embeddings = model.get_embeddings(inputs, **kwargs)
    embeddings = [e.values for e in embeddings]

    for node, embedding in zip(nodes, embeddings):
        node.embedding = embedding
        
    return nodes
    

def _generate_embeddings(
    doc_lookup: dict[str, dict],
    model: TextEmbeddingModel,
    batch_size: int = 16 
):
    all_nodes = []
    for uri, data in doc_lookup.items():
        nodes = data['nodes']
        all_nodes.extend(nodes)

    node_batches = [all_nodes[i : i + batch_size] for i in range(0, len(all_nodes), batch_size)]

    all_embedded_nodes = []
    for i, node_batch in enumerate(node_batches):
        logger.info(f'Embedding batch {i+1}/{len(node_batches)}')

        embedded_nodes = _embed_nodes(node_batch, model)
        all_embedded_nodes.extend(embedded_nodes)

    return doc_lookup


def get_embeddings(
    files: list[str],
    fs: GCSFileSystem,
    gcs_metadata: dict[str, dict],
    model: TextEmbeddingModel
) -> dict[str, dict]:
    reader = SimpleDirectoryReader(
        input_files=files,
        fs=fs
    )
    docs: list[Document] = reader.load_data()

    doc_lookup = _get_doc_lookup(docs=docs)
    doc_lookup = _attach_gcs_metadata_to_doc_lookup(
        doc_lookup=doc_lookup,
        gcs_metadata=gcs_metadata
    )
    doc_lookup = _get_nodes(doc_lookup=doc_lookup)

    doc_lookup = _generate_embeddings(
        doc_lookup=doc_lookup,
        model=model
    )
    return doc_lookup

def embed_empty_node(
    model: TextEmbeddingModel,
    task: str = "RETRIEVAL_DOCUMENT",
    dimensionality: int = 768
):
    node = TextNode()
    node.text = ' '
    texts = [node.text]
    inputs = [TextEmbeddingInput(text, task) for text in texts]
    kwargs = dict(output_dimensionality=dimensionality) if dimensionality else {}
    embeddings = model.get_embeddings(inputs, **kwargs)
    embeddings = [e.values for e in embeddings]
    node.embedding = embeddings[0]
    return node  


def upsert_vectors(
    doc_lookup: dict[str, dict],
    index: Index,
    id_prefix: str,
    model: TextEmbeddingModel
):
    batch_upsert_ts = datetime.now(tz=timezone.utc)
    batch_upsert_ts_int = int(batch_upsert_ts.timestamp())
    batch_upsert_ts_str = batch_upsert_ts.isoformat()

    records = []
    for uri, data in doc_lookup.items():
        record_id = f'{id_prefix}##{uri}'
        gcs_metadata = data['gcs_metadata']
        _record_metadata = {
            'kb_id': id_prefix,
            'pinecone_upsert_ts_epoch': batch_upsert_ts_int,
            'pinecone_upsert_ts_iso': batch_upsert_ts_str,
            'latest_commit': gcs_metadata.get('latest_commit'),
            'latest_commit_ts': gcs_metadata.get('latest_commit_ts'),
        }

        folder_prefix = uri.split('/')[1]
        if folder_prefix == 'pdf':
            _record_metadata.update({
                'repo_path': '/'.join(uri.split('/')[2:]).replace('.pdf', '.md'),
                'pdf_uri': uri
            })
        elif folder_prefix == 'descriptions':
            _record_metadata.update({
                'image_description': True,
                'repo_path': '/'.join(uri.split('/')[2:-1]).replace('.pdf', '.md'),
                'description_uri': uri,
                'pdf_uri': f'{uri.split("/")[0]}/pdf/' + '/'.join(uri.split('/')[2:-1])
            })
        
        if data['nodes']:
            for i, node in enumerate(data['nodes']):
                record_metadata = _record_metadata.copy()
                record_metadata.update({'text': node.text})
                record = {
                    'id': f'{record_id}##{i}',
                    'values': node.embedding,
                    'metadata': record_metadata
                }
                records.append(record)

        else:  # when file has no text (e.g. PDF with only images)
            node = embed_empty_node(model)
            record_metadata = _record_metadata.copy()
            record_metadata.update({'text': node.text})
            record = {
                'id': f'{record_id}##0',
                'values': node.embedding,
                'metadata': record_metadata
            }
            records.append(record)        
        
    batch_size = 100
    record_batches = [records[i : i + batch_size] for i in range(0, len(records), batch_size)]
    for i, batch in enumerate(record_batches):
        logger.info(f'Upserting batch {i+1}/{len(record_batches)}')
        response = index.upsert(batch)
        logger.info(str(response))



def _main(
    bucket_name: str,
    index_name: str,
    batch_size: int,
    cache_freshness: int
):
    fs, gcs, pc, fs_db = init_clients(project=c.PROJECT_ID)
    index = pc.Index(index_name)

    uris = list_uris(fs=fs, bucket=bucket_name)


    logger.info('Getting GCS metadata...')
    gcs_meta = get_metadata(
        gcs=gcs,
        fs_db=fs_db,
        collection_name=c.FS_COLLECTION_NAME,
        bucket_name=bucket_name,
        uris=uris,
        freshness_minutes=cache_freshness
    )

    model = TextEmbeddingModel.from_pretrained('text-embedding-004')
    id_prefix = f'kb-github-{bucket_name}'

    directives = get_directives(
        index=index,
        gcs_meta=gcs_meta,
        id_prefix=id_prefix
    )

    if directives['deletes']:
        logger.info(f'Deleting {len(directives["deletes"])} records from Pinecone')
        del_batch_size = 1000
        del_batches = [directives['deletes'][i : i + del_batch_size] for i in range(0, len(directives['deletes']), del_batch_size)]
        for i, batch in enumerate(del_batches):
            logger.info(f'Deleting batch {i+1}/{len(del_batches)}')
            response = index.delete(ids=batch)

    else:
        logger.info('No records to delete from Pinecone')
    
    if directives['inserts']:
        files = directives['inserts']
        logger.info(f'Found {len(files)} total files to load into Pinecone')
    else:
        logger.info('No new files to insert into Pinecone. Exiting...')
        return {'result': 'DONE'}
    
    batch_size = batch_size if len(files) > batch_size else len(files)
    batch = files[:batch_size]
    logger.log_struct(
        message=f'Processing {len(batch)} files...',
        files=batch
    )
    doc_lookup = get_embeddings(
        files=batch,
        fs=fs,
        gcs_metadata=gcs_meta,
        model=model
    )
    upsert_vectors(
        doc_lookup=doc_lookup,
        index=index,
        id_prefix=id_prefix,
        model=model
    )
    logger.info('Batch upsert complete')
    return {'result': 'CONTINUE'}

@app.post('/load-pinecone')
def load_pinecone(req: LoadPineconeRequest):
    try:
        return _main(
            bucket_name=req.bucket_name,
            index_name=req.index_name,
            batch_size=req.batch_size,
            cache_freshness=req.cache_freshness
        )
    except Exception as e:
        logger.error(str(e))
        return {'error': str(e)}


if __name__ == '__main__':

    # FOR LOCAL TESTING

    from dotenv import load_dotenv
    load_dotenv()

    BUCKET_NAME = 'bd-gh-data-spot-sdk'
    INDEX_NAME = 'genai-sandbox'
    CACHE_FRESHNESS_MINUTES = 10
    BATCH_SIZE = 50

    _main(
        bucket_name=BUCKET_NAME,
        index_name=INDEX_NAME,
        batch_size=BATCH_SIZE,
        cache_freshness=CACHE_FRESHNESS_MINUTES
    )

