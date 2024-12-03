import os
from datetime import datetime, timezone, timedelta
from itertools import chain

from gcsfs import GCSFileSystem
from google.cloud import storage, aiplatform

from pinecone import Pinecone, Index
from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import BaseNode, Document, TextNode
from llama_index.core.node_parser import SentenceSplitter
from vertexai.preview.language_models import TextEmbeddingModel, TextEmbeddingInput

from . import request_models


def init_clients(project: str) -> tuple[GCSFileSystem, storage.Client, Pinecone]:
    
    required_env_variables = [
        'PINECONE_API_KEY',
        'GCP_REGION',
    ]
    for var in required_env_variables:
        if not os.getenv(var):
            msg = f'{var} not found in environment variables. Required environment variables: {required_env_variables}'
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
    

def _get_doc_lookup(
    docs: list[Document]
) -> dict[str, list[Document]]:
    lookup = {}
    for doc in docs:
        uri = doc.metadata['file_path']
        if lookup.get(uri):
            lookup[uri]['documents'].append(doc)
        else:
            lookup[uri] = {'documents': [doc]}
    return lookup

def _node_parser(documents: list[Document]):
    node_parser = SentenceSplitter(
        chunk_size=1024,
        chunk_overlap=50
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
        embedded_nodes = _embed_nodes(node_batch, model)
        all_embedded_nodes.extend(embedded_nodes)

    return doc_lookup

def get_embeddings(
    files: list[str],
    fs: GCSFileSystem,
    model: TextEmbeddingModel
) -> dict[str, dict]:
    reader = SimpleDirectoryReader(
        input_files=files,
        fs=fs
    )
    docs: list[Document] = reader.load_data()

    doc_lookup = _get_doc_lookup(docs)
    doc_lookup = _get_nodes(doc_lookup)
    doc_lookup = _generate_embeddings(doc_lookup, model, 16)
    return doc_lookup

def embed_empty_node(
    model: TextEmbeddingModel,
    task: str = "RETRIEVAL_DOCUMENT",
    dimensionality: int = 768
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

def upsert_vectors(
    doc_lookup: dict[str, dict],
    index: Index,
    kb_id: str,
    model: TextEmbeddingModel
):
    batch_upsert_ts = datetime.now(tz=timezone.utc)
    batch_upsert_ts_int = int(batch_upsert_ts.timestamp())
    batch_upsert_ts_iso = batch_upsert_ts.isoformat()

    records = []
    for uri, data in doc_lookup.items():
        record_id_prefix = f'{kb_id}##{uri.replace(" ", "_")}'
        _record_metadata = {
            'kb_id': kb_id,
            'user_upload': True,
            'pinecone_upsert_ts_epoch': batch_upsert_ts_int,
            'pinecone_upsert_ts_iso': batch_upsert_ts_iso,
            'gcs_uri': uri
        }
        if data['nodes']:
            for i, node in enumerate(data['nodes']):
                record_metadata = _record_metadata.copy()
                record_metadata.update({'text': node.text})
                record_id = f'{record_id_prefix}##{i}'
                record = {
                    'id': record_id,
                    'values': node.embedding,
                    'metadata': record_metadata,
                }
                records.append(record)
        else:
            node = embed_empty_node(model)
            record_metadata = _record_metadata.copy()
            record_metadata.update({'text': node.text})
            record = {
                'id': f'{record_id_prefix}##0',
                'values': node.embedding,
                'metadata': record_metadata
            }
            records.append(record)

    batch_size = 100
    record_batches = [records[i : i + batch_size] for i in range(0, len(records), batch_size)]
    for i, record_batch in enumerate(record_batches):
        print(f'Upserting batch {i+1} of {len(record_batches)}')
        resp = index.upsert(record_batch)
        print(str(resp))
    


def upload_files(
    upload_requests: list[request_models.FileUploadRequest],
):
    fs, gcs, pc = init_clients(project=os.environ['GCP_PROJECT'])
    
    # init pinecone index
    index: Index = pc.Index(name=os.getenv('PINECONE_INDEX_NAME'))
    

    # todo: get directives
    files = [req.gcs_uri.replace(f"gs://", "", 1) for req in upload_requests]

    # generate embeddings
    model = TextEmbeddingModel.from_pretrained('text-embedding-004')
    embeddings = get_embeddings(files, fs, model)

    # load to pinecone
    upsert_vectors(
        doc_lookup=embeddings,
        index=index,
        kb_id=upload_requests[0].kb_id,  # kb_id is the same for all requests per batch
        model=model
    )


def delete_files(
    delete_requests: list[request_models.FileDeleteRequest],
):
    pc = Pinecone(os.getenv('PINECONE_API_KEY'))
    index = pc.Index(name=os.getenv('PINECONE_INDEX_NAME'))

    id_prefixes = [f'{req.kb_id}##{req.gcs_uri.replace(f"gs://","", 1).replace(" ", "_")}' for req in delete_requests]
    
    ids_to_delete = []
    for prefix in id_prefixes:
        ids_to_delete.extend(index.list(prefix=prefix))

    max_batch_size = 1000
    batches = [ids_to_delete[i : i + max_batch_size] for i in range(0, len(ids_to_delete), max_batch_size)]
    for i, batch in enumerate(batches):
        print(f'Deleting batch {i+1} of {len(batches)}')
        index.delete(ids=batch)
    
    


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()

    fs = GCSFileSystem(project=os.environ['GCP_PROJECT'], token=os.environ['GOOGLE_APPLICATION_CREDENTIALS'])

    # args
    KB_ID = ''
    URIS = []

    reqs = [request_models.FileDeleteRequest(kb_id=KB_ID, gcs_uri=uri, file_id='foo') for uri in URIS] 
    
    # upload_files(reqs)
    # delete_files(reqs)
    



