
# gcloud artifacts repositories create drive-sync-service \
#     --repository-format docker \
#     --location us-central1 \
#     --project bd-genai-internal

gcloud builds submit \
    --region=us-central1 \
    --tag us-central1-docker.pkg.dev/bd-genai-internal/drive-sync-service/drive-sync-service:latest

gcloud run jobs deploy drive-sync-service \
    --region=us-central1 \
    --image us-central1-docker.pkg.dev/bd-genai-internal/drive-sync-service/drive-sync-service:latest \
    --max-retries=0 \
    --task-timeout=1h \
    --memory 2Gi