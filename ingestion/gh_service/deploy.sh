
gcloud builds submit \
    --region=us-central1 \
    --tag us-central1-docker.pkg.dev/bd-genai-internal/github-ingest-service/gh_service:latest

gcloud run jobs deploy gh-service \
    --region=us-central1 \
    --image us-central1-docker.pkg.dev/bd-genai-internal/github-ingest-service/gh_service:latest