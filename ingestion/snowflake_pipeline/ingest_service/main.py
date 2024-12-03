import os
from pathlib import Path
import yaml
from itertools import chain
from datetime import datetime
from time import sleep, time
import traceback

import pandas as pd

from pinecone import Pinecone, Index
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.schema import Document
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core.node_parser import SentenceSplitter

from snowflake_client import SFConnection
from log import CloudLogger
import constants as c
import data_cleaning as dc
from models import LoadPineconeRequest

from fastapi import FastAPI

logger = CloudLogger(log_name=c.LOGGER_NAME, project_id=c.PROJECT_ID)
app = FastAPI()

def _truncate_list(l: list, n: int) -> list:
    """Used for reducing size of log data"""
    return l[:n] if len(l) > n else l

def get_documents_from_df(df: pd.DataFrame) -> list[Document]:

    df['CDC_TIMESTAMP_ISO'] = df['CDC_TIMESTAMP']
    df['CDC_TIMESTAMP_EPOCH'] = df['CDC_TIMESTAMP'].apply(
        lambda ts_iso: datetime.fromisoformat(ts_iso).timestamp()
    )
    df = df.drop(columns=['CDC_TIMESTAMP'])

    metadata_cols = [col for col in df.columns if col not in ['PINECONE_TEXT', 'PK']]

    documents = []
    for _, row in df.iterrows():
        documents.append(Document(
            text=row['PINECONE_TEXT'],
            metadata={col: row[col] for col in metadata_cols},
            id_=row['PK']
        ))
    return documents

def get_nodes_from_documents(
    docs: list[Document],
    snowflake_source: str,
    kb_id: str
):
    node_parser = SentenceSplitter(
        chunk_size=512,
        chunk_overlap=50
    )
    nodes = node_parser.get_nodes_from_documents(docs)

    doc_node_mapper = {}
    for node in nodes:
        doc_id = node.source_node.node_id
        if doc_id in doc_node_mapper:
            doc_node_mapper[doc_id].append(node)
        else:
            doc_node_mapper[doc_id] = [node]
    
    updated_nodes = []
    for doc_id, _nodes in doc_node_mapper.items():
        for i, node in enumerate(_nodes):
            cdc_ts = node.metadata['CDC_TIMESTAMP_ISO']
            node_id = f'{kb_id}##{snowflake_source}##{doc_id}##{cdc_ts}##{i}'
            node.id_ = node_id
            node.metadata.update({
                'kb_id': kb_id,
                # 'text': node.text
            })
            updated_nodes.append(node)

    return updated_nodes


def get_pinecone_records(
    index: Index,
    snowflake_source: str,
    kb_id: str
) -> dict[str, list[str]]:
    id_prefix = f'{kb_id}##{snowflake_source}##'
    records = list(chain.from_iterable(index.list(prefix=id_prefix)))
    document_id_lookup = {}
    for record in records:
        doc_id = record.split('##')[2]
        if doc_id in document_id_lookup:
            document_id_lookup[doc_id].append(record)
        else:
            document_id_lookup[doc_id] = [record]
    return document_id_lookup

def _get_upsert_df(
    df: pd.DataFrame,
    pc_records: dict,
    docs_to_compare: list[str]
) -> pd.DataFrame:

    docs_to_upsert = []
    for doc_id in docs_to_compare:
        pc_record = pc_records[doc_id][0]
        pc_timestamp = datetime.fromisoformat(pc_record.split('##')[3])

        source_timestamp = df.loc[df['PK'] == doc_id, 'CDC_TIMESTAMP'].values[0]
        source_timestamp = datetime.fromisoformat(source_timestamp)

        if source_timestamp > pc_timestamp:
            docs_to_upsert.append(doc_id)
    
    return df[df['PK'].isin(docs_to_upsert)]


def get_directives(
    source_df: pd.DataFrame,
    kb_id: str,
    index: Index,
    snowflake_source: str,
) -> list[tuple[str, Document]]:

    pc_records = get_pinecone_records(
        index=index,
        snowflake_source=snowflake_source,
        kb_id=kb_id
    )

    # get deletes - documents in pinecone but not in snowflake
    pc_documents = list(pc_records.keys())
    sf_documents = source_df['PK'].tolist()
    deletes = []
    for doc in pc_documents:
        if doc not in sf_documents:
            deletes.extend(pc_records[doc])
    if deletes:
        logger.log_struct(
            message=f'Deleting {len(deletes)} from Pinecone',
            # record_ids_head=_truncate_list(deletes, 10)
        )
        delete_batch_size = 1000
        delete_batches = [deletes[i:i+delete_batch_size] for i in range(0, len(deletes), delete_batch_size)]
        for i, batch in enumerate(delete_batches):
            logger.info(f'Deleting batch {i+1} of {len(delete_batches)}')
            index.delete(ids=batch)
    else:
        logger.info('No records to delete from Pinecone')
    
    # get inserts - documents in snowflake but not in pinecone
    df_inserts = source_df[~source_df['PK'].isin(pc_documents)]
    if len(df_inserts.index) > 0:
        logger.info(f'Found {len(df_inserts.index)} new documents to insert')
        docs_insert = get_documents_from_df(df_inserts)
    else:
        logger.info('No new documents to insert')
        docs_insert = []
    
    # get upserts - compare cdc timestamps
    docs_to_compare = list(set(pc_documents).intersection(set(sf_documents)))
    df_upserts = _get_upsert_df(
        df=source_df,
        pc_records=pc_records,
        docs_to_compare=docs_to_compare,
    )
    if len(df_upserts.index) > 0:
        logger.log_struct(
            message=f'Found {len(df_upserts.index)} documents to update',
            # ids_first_10=_truncate_list(df_upserts['PK'].tolist(), 10)
        )
        docs_upsert = get_documents_from_df(df_upserts)
    else:
        logger.info('No documents to upsert')
        docs_upsert = []

    directives = [('insert', doc) for doc in docs_insert] + [('upsert', doc) for doc in docs_upsert] 

    return directives


def load_batch(
    directives: list[tuple[str, Document]],
    index: Index,
    snowflake_source: str,
    kb_id: str
):
    
    # for upserts, remove associated records
    deletes = {}
    for action, doc in directives:
        if action == 'upsert': 
            id_prefix = f'{kb_id}##{snowflake_source}##{doc.id_}'
            record_ids = list(chain.from_iterable(index.list(prefix=id_prefix)))
            deletes[doc.id_] = record_ids
    if deletes:
        logger.log_struct(
            message=f'Deleting records associated with {len(deletes)} documents to upsert.',
            # documents_first_10=_truncate_list(deletes, 10)
        )
        index.delete(ids=list(chain.from_iterable(deletes.values())))

    # get nodes
    nodes = get_nodes_from_documents(
        docs=[doc for _, doc in directives],
        snowflake_source=snowflake_source,
        kb_id=kb_id
    )

    # upsert nodes
    Settings.embed_model = GeminiEmbedding(
        model_name='models/text-embedding-004',
        embed_batch_size=16,
        api_key=os.getenv('GOOGLE_API_KEY')
    )
    vector_store = PineconeVectorStore(
        pinecone_index=index,
        add_sparse_vector=True,
    )
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store
    )
    batch_size = 100
    batches = [nodes[i:i+batch_size] for i in range(0, len(nodes), batch_size)]
    for i, batch in enumerate(batches):
        logger.log_struct(
            message=f'Upserting batch {i+1}/{len(batches)}',
            # record_ids_first_10=_truncate_list([node.id_ for node in batch], 10)
        )
        VectorStoreIndex(
            nodes=batch,
            # use_async=True,
            storage_context=storage_context
        )

def _delete_records_by_id_prefix(
    index: Index,
    id_prefix: str,
    timeout: int
):
    ids = list(chain.from_iterable(index.list(prefix=id_prefix)))

    delete_batch = 1000
    batches = [ids[i:i+delete_batch] for i in range(0, len(ids), delete_batch)]
    for i, batch in enumerate(batches):
        logger.info(f'Deleting batch {i+1} of {len(batches)}')
        index.delete(ids=batch)
    
    count_after = len(list(chain.from_iterable(index.list(prefix=id_prefix))))
    logger.info(f'Records pending deletion: {count_after}')

    i = 0
    while count_after != 0:
        sleep(1)
        count_after = len(list(chain.from_iterable(index.list(prefix=id_prefix))))
        logger.info(f'({i}) Records pending deletion: {count_after}')
        i += 1
        if i >= timeout:
            logger.error(
                f'Failed to delete all records with prefix `{id_prefix}` after {timeout} seconds.'
                f'Remaining records: {count_after}'
            )
            break
    
    
def truncate_source(
    index: Index,
    snowflake_source: str,
    kb_id: str
) -> None:
    
    id_prefix = f'{kb_id}##{snowflake_source}##'
    ids = list(chain.from_iterable(index.list(prefix=id_prefix)))
    if not ids:
        logger.info(f'No records to truncate with prefix `{id_prefix}`')
        return
    
    logger.info(f'Truncating {len(ids)} records from source `{snowflake_source}`')
    _delete_records_by_id_prefix(
        index=index,
        id_prefix=id_prefix,
        timeout=30
    )


def _main(
    snowflake_source: str,
    batch_size: int,
    truncate: bool = False
): 
    
    logger.info(f'Starting snowflake ingest job for source: `{snowflake_source}`')

    sf = SFConnection.from_env()
    try:
        df, kb_id = dc.get_data_source(snowflake_source, sf)
    except Exception as e:
        logger.error(f'Error getting data from Snowflake: {str(e)}')
        raise 
    logger.set_label('kb_id', kb_id)

    pc = Pinecone(os.getenv('PINECONE_API_KEY'))
    index = pc.Index(name=os.getenv('PINECONE_INDEX_NAME'))

    if truncate:
        logger.warning(f'Prior to load: Removing all records from index for source `{snowflake_source}`')
        truncate_source(index=index, snowflake_source=snowflake_source, kb_id=kb_id)


    directives: list[tuple[str, Document]] = get_directives(
        source_df=df,
        kb_id=kb_id,
        index=index,
        snowflake_source=snowflake_source
    )
    if not directives:
        logger.info('No directives to process. Exiting...')
        return {'result': 'DONE'}

    logger.info(f'Found {len(directives)} directives to process')
    batch_size = batch_size if batch_size < len(directives) else len(directives)
    batch = directives[:batch_size]

    logger.log_struct(
        message=f'Processing batch of size {batch_size}',
        # batch_ids_first_10=_truncate_list([doc.id_ for _, doc in batch], 10)
    )
    load_batch(
        directives=batch,
        index=index,
        snowflake_source=snowflake_source,
        kb_id=kb_id
    )
    logger.info('Job complete')
    return {'result': 'CONTINUE'}


@app.post('/load-pinecone')
def load_pinecone(req: LoadPineconeRequest):
    logger.set_label('snowflake_source', req.snowflake_source)
    logger.set_label('pinecone_index_name', os.environ['PINECONE_INDEX_NAME'])
    logger.set_label('batch_size', str(req.batch_size))
    logger.set_label('truncate', str(req.truncate))
    try:
        start_time = time()
        result = _main(
            snowflake_source=req.snowflake_source,
            batch_size=req.batch_size,
            truncate=req.truncate
        )
        end_time = time()
        logger.info(f'Execution time: {end_time - start_time} seconds')
        return result
    
    except Exception as e:
        logger.log_struct(
            message=f'Error running job: {str(e)}',
            severity='ERROR',
            traceback=traceback.format_exc()
        )
        return {'error': str(e)}


if __name__ == '__main__':

    # FOR RUNNIG LOCALLY

    from dotenv import load_dotenv
    from time import time
    load_dotenv()

    # ARGS

    SF_SOURCE = ''
    BATCH_SIZE = 10
    TRUNCATE = False

    start = time()
    _main(
        snowflake_source=SF_SOURCE,
        batch_size=BATCH_SIZE,
        truncate=TRUNCATE
    )
    end = time()
    print(f'Execution time: {end-start} seconds')

