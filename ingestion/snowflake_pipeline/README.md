# Snowflake Ingestion Pipeline

This pipeline is used for ingesting data related to Salesforce, which is stored in Snowflake.

## Integrating Additional Queries/Tables

It is possible to integrate additional knowledge bases as defined by an arbitrary query in Snowflake. 

1. Define a function in `data_cleaning.py` which returns a DataFrame that contains the following columns:
- `PK`: The "primary key" of the dataframe (any unique value works)
- `PINECONE_TEXT`: the text that will be indexed. This will usually be the concatenated values of other fields returned by the query (see the function `dwcs_salesforce_knowledge` as an example)
- `CDC_TIMESTAMP` This should contain the timestamp values that will be used for determining change data capture. This column should be a string in the ISO format. 

2. Once the function is defined, add a new entry to the `DATA_SOURCE_MAPPER` dictionary in `data_cleaning.py`. The key should be a descriptive name for the datasource (e.g. `dwcs.salesforce.knowledge`), the value will be another dictionary which contains a reference to the function defined in step 1, and a knowledge base id (`kb_id`) which will be used to identify the data source within Pinecone, and surface it on the frontend. 

3. Once the entry has been created in the `DATA_SOURCE_MAPPER`, the main function ()`_main()` within the `main.py`) file can be executed with the name of the data source being passed as the `snowflake_source` argument.

4. Once the process has completed and the data has been indexed in snowflake, a firestore `knowledge_base` object must be created such that the knowledge base is exposed to the application frontend. See the steps outlined [here](https://docs.google.com/document/d/1wU2fyZZ3p4RWSAKBeIYZiQf6onMAVdF_9YvovYNmg6c/edit?tab=t.0#heading=h.tc57rfdx3opa) for instructions on how to do this. Note that the linked documentation is discussing integrating a drive knowledge base, but the process is exactly the same for a snowflake KB. 
