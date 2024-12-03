from __future__ import annotations
from functools import partial

import pandas as pd
from html2text import html2text

from llama_index.core.schema import Document

from snowflake_client import SFConnection


def _concat_columns_with_header(row, columns):
    result = ''
    for col in columns:
        result += f'{col}: {row[col]}\n\n'
    return result.strip()


def dwcs_salesforce_knowledge(
    sf_client: SFConnection
) -> pd.DataFrame:
    
    table = 'dwcs.salesforce.knowledge'
    pk_cols = ['ID']
    text_cols = ['TITLE', 'SUMMARY', 'DETAILS__C']
    metadata_cols = ['TITLE', 'SUMMARY', 'FULL_ARTICLE_LINK__C']
    cdc_column = 'LASTMODIFIEDDATE'

    all_cols = list(set(pk_cols + text_cols + metadata_cols + [cdc_column]))
    query = f'''
    SELECT
        {', '.join(all_cols)}
    FROM {table}
    WHERE publishstatus='Online';
    '''
    df = sf_client.query(query)

    df['DETAILS__C'] = df['DETAILS__C'].apply(html2text)
    df = df.fillna(' ')

    strf = '%Y-%m-%dT%H:%M:%S+00:00'
    df[cdc_column] = pd.to_datetime(df[cdc_column], utc=True)
    df[cdc_column] = df[cdc_column].dt.strftime(strf)
    df = df.rename(columns={
        cdc_column: 'CDC_TIMESTAMP',
        'ID': 'PK'
    })

    df['PINECONE_TEXT'] = df.apply(
        lambda row: _concat_columns_with_header(row, text_cols),
        axis=1
    )
    df = df[[c for c in df.columns if c != 'DETAILS__C']]

    return df

def genai_stretchfaults(
    sf_client: SFConnection
) -> pd.DataFrame:
    
    table = 'genai.pipelines.vw_stretch_faults'
    pk_cols = ['ID']
    text_cols = ['PTEXT']
    metadata_cols = ['PTEXT']
    cdc_column = 'CDC_TIMESTAMP'

    all_cols = list(set(pk_cols + text_cols + metadata_cols + [cdc_column]))
    query = f'''
    SELECT
        {', '.join(all_cols)}
    FROM {table}
    ;
    '''
    df = sf_client.query(query)

    df['PTEXT'] = df['PTEXT'].apply(html2text)
    df = df.fillna(' ')

    strf = '%Y-%m-%dT%H:%M:%S+00:00'
    df[cdc_column] = pd.to_datetime(df[cdc_column], utc=True)
    df[cdc_column] = df[cdc_column].dt.strftime(strf)
    df = df.rename(columns={
        cdc_column: 'CDC_TIMESTAMP',
        'ID': 'PK'
    })

    df['PINECONE_TEXT'] = df.apply(
        lambda row: _concat_columns_with_header(row, text_cols),
        axis=1
    )
    df = df[[c for c in df.columns if c != 'PTEXT']]

    return df


def dwcs_salesforce_case(
    sf_client: SFConnection,
    is_closed: bool
) -> pd.DataFrame:
    table = 'dwcs.salesforce.case'
    pk_cols = ['ID']
    text_cols = [
        'CASENUMBER', 'STATUS', 'ISCLOSED', 'ORIGIN',
        'CREATEDDATE', 'SUBJECT', 'DESCRIPTION',
        'CLOSURE_NOTES__C', 'REASON__C', 'SUPPLIEDNAME',
        'SUPPLIEDEMAIL', 'TYPE', 'PRIORITY', 'CONTACTPHONE',
        'CONTACTEMAIL', 'CONTACTMOBILE', 'CASE_OWNER_EMAIL__C',
        'THREADID__C', 'ENGAGEMENT_TYPE__C'
    ]
    metadata_cols = [
        'ISCLOSED', 'ID'
    ]
    cdc_column = 'LASTMODIFIEDDATE'
    query = f'''
    WITH DEDUPE AS (
        SELECT {', '.join(pk_cols + text_cols + [cdc_column])},
            ROW_NUMBER() OVER (PARTITION BY {pk_cols[0]} ORDER BY {cdc_column} DESC) AS RN
        FROM {table} 
        WHERE STATUS != 'BD_Cancelled'
    )
    SELECT * EXCLUDE(RN)
    FROM DEDUPE
    WHERE RN = 1
    '''
    if is_closed:
        query += f'''
        AND CREATEDDATE > DATEADD(year, -1, CURRENT_DATE)
        AND ISCLOSED;
        '''
    else:
        query += ' AND NOT ISCLOSED;'

    df = sf_client.query(query)

    df = df.fillna(' ')
 
    strf = '%Y-%m-%dT%H:%M:%S+00:00'
    df['CDC_TIMESTAMP'] = pd.to_datetime(df[cdc_column], utc=True)
    df['CDC_TIMESTAMP'] = df['CDC_TIMESTAMP'].dt.strftime(strf)

    df['PINECONE_TEXT'] = df.apply(
        lambda row: _concat_columns_with_header(row, text_cols + [cdc_column]),
        axis=1
    )

    df['PK'] = df['ID']

    df = df[[c for c in df.columns if c in(['PK', 'PINECONE_TEXT', 'CDC_TIMESTAMP'] + metadata_cols)]]

    return df

    


DATA_SOURCE_MAPPER = {
    'dwcs.salesforce.knowledge': {
        'func': dwcs_salesforce_knowledge,
        'kb_id': 'kb-sf-knowledge'
    },
        'genai.pipelines.vw_stretch_faults': {
        'func': genai_stretchfaults,
        'kb_id': 'Stretch-Faults'
    },
    'dwcs.salesforce.case__open': {
        'func': partial(dwcs_salesforce_case, is_closed=False),
        'kb_id': 'kb-sf-case-open'
    },
    'dwcs.salesforce.case__closed': {
        'func': partial(dwcs_salesforce_case, is_closed=True),
        'kb_id': 'kb-sf-case-closed'
    }
}

def get_data_source(
    data_source: str,
    sf: SFConnection
) -> tuple[pd.DataFrame, str]:
    
    try:
        df = DATA_SOURCE_MAPPER[data_source]['func'](sf)
        kb_id = DATA_SOURCE_MAPPER[data_source]['kb_id']
    except KeyError:
        raise ValueError(f'No data cleaning function found for source `{data_source}`')
    
    required_cols = ['PK', 'PINECONE_TEXT', 'CDC_TIMESTAMP']
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        raise ValueError(f'Missing required columns: {missing_cols}')
    
    # assert PK is unique
    if df['PK'].nunique() != df.shape[0]:
        raise ValueError('PK is not unique')
    
    return df, kb_id
