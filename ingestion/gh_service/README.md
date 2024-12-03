# GitHub Sync Service

This is a service which points at a public GitHub repo, converts all markdown files in the repo to PDF, and loads those PDF files into a specified GCS bucket.

The folder structure of the GCS bucket mirrors that of the repository.

## Change Data Capture

To capture newly uploaded, updated or deleted files, the most recent commit timestamp of a file in github is compared to the most recent commit timestamp of its analog in GCS (if the file exists in GCS). Whenever a file is uploaded or updated in GCS, its object metadata is updated to reflect the most recent commit timestamp.

## Running the Script

First, initialize the environment by building the docker image defined in the Dockefile, and running the image in a container. 

To run this script locally, there are only two required arguments:
```
--repo_url : the url of the repository to be processed
--bucket : the GCS bucket where the processed files will land
```

For example:
```
python convert.py \
    --repo_url https://github.com/boston-dynamics/spot-sdk \
    --bucket bd-gh-data-spot-sdk
```
