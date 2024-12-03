# PDF Image Description Service

This service is responsible for extracting images from PDF files, and generating textual descriptions of the images using Gemini multimodal language model: `gemini-1.5-flash-001`.

## Request Model

This service is implemented as a single FastAPI endpoint which accepts the following as a request body:


```
# ImageDescriptionRequest

source_uri : GCS uri to source PDF file
target_folder_uri : uri of folder to contain image descriptions as individual text files
```

The endpoint takes a list of ImageDescriptionRequest objects (see `models.py`).