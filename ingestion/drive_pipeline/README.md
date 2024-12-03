# Google Drive Ingest Pipeline

This pipeline is used for ingesting data from Google Drive, pre-processing the data, and indexing it in Pinecone for consumption by the GenAI RAG application. 

The steps of the pipeline are as follows:

1. **File sync:** Files from the target Google Drive folder are synced to the staging GCS bucket. Necessary updates/deletes/inserts are determined based on the modifiedTimeStamp returned from the Google Drive API.
2. **DOCX to PDF conversion:** All DOCX files contained in the raw storage folder are converted to PDF. 
3. **PDF Image Description:** All newly staged PDF files are run through the image description service, with outputs being written out as text files in a subfolder of the staging bucket.
4. **Upsert to Pinecone:** CDC logic determines which files should be loaded or removed from pinecone. All files to be loaded are then chunked, embedded, and upserted to pinecone.

These steps and services are orchestrated using **Cloud Workflows**. The workflow definition can be found at the root of this directory at `workflow.yaml`.

## Pointing at another google drive folder

To incorporate additional drive folders into the ingestion pipeline, follow the steps described in the [Data Ingestion Knowledge Transfer documentation](https://docs.google.com/document/d/1wU2fyZZ3p4RWSAKBeIYZiQf6onMAVdF_9YvovYNmg6c/edit?tab=t.0#heading=h.tc57rfdx3opa).
