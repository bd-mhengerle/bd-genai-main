# GitHub Ingest Pipeline

The GitHub ingestion pipeline takes the following steps:
1. **File sync:** Clone target repository, determine which files need to be inserted/updated/deleted from GCS staging (based on latest commit timestamp), convert all files to be loaded to PDF, and load PDFs to GCS staging area.
2. **PDF Image Description:** For any newly staged PDFs, images are extracted and run through an image description service, using the gemini-1.5-flash-001 multimodal model. These image descriptions are written as text files to a subfolder of the GCS staging bucket.
3. **Upsert to Pinecone:** Based on the PDFs and image descriptions in GCS, files are chunked, embeddings are generated, and the embeddings are upserted to Pinecone.

## Ingesting Additional Repositories

Currently, only the `spot-sdk` repository is being ingested into the application. Ingesting additional repositories is as straightforward as passing the URL of the desired repository to the `repo_url` argument of the Cloud Workflow (as defined in `workflow.yaml`). Note that the repository must be public. 