gcloud run deploy snowflake-pipeline-load-pinecone \
    --source . \
    --project bd-genai-internal \
    --no-allow-unauthenticated \
    --region us-central1 \
    --env-vars-file env.yaml \
    --memory 1Gi \
    --concurrency 1