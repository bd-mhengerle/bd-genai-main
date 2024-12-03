
gcloud functions deploy drive_pipeline_convert_docx \
    --no-allow-unauthenticated \
    --trigger-http \
    --runtime=python310 \
    --region=us-central1 \
    --source=. \
    --entry-point=main \
    --project=bd-genai-internal \
    --timeout=540s \
    --memory=1Gi
    