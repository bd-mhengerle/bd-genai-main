
gcloud functions deploy cr_job_runner \
    --no-allow-unauthenticated \
    --trigger-http \
    --runtime=python310 \
    --region=us-central1 \
    --source=. \
    --entry-point=main \
    --project=bd-genai-internal \
    --service-account=genai-cr-job-runner-sa@bd-genai-internal.iam.gserviceaccount.com