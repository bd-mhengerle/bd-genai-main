gcloud run deploy image-description \
    --source . \
    --project bd-genai-internal \
    --no-allow-unauthenticated \
    --region us-central1 \
    --memory 2Gi
    