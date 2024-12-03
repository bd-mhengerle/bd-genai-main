gcloud run deploy docx-to-pdf \
    --source . \
    --project bd-genai-internal \
    --no-allow-unauthenticated \
    --region us-central1 \
    --memory 2Gi