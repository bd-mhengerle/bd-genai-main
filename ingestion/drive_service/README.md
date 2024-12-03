# Google Drive Sync Service

This is a service which synchronizes the state of a Google Drive folder with a GCS folder.

## Change Data Capture

In order to correctly capture newly created, updated or deleted documents, the service relies on metadata pulled from each file, which is then persisted to GCS as object metdata. Specifically, the `modifiedTimeStamp` is used to compare the last modified time of a file in GCS to its counterpart in Drive. 

Files are uniquely identified using their `fileId` (rather than the file name). This is because Google Drive permits duplicative file names, whereas GCS doesn't. 

## Calling The Script

The script has 3 required arguments and one optional argument:
```
--principal : the email address of the principal account which is using service account impersonation to access the drive folder. This account must be granted "reader" permissions on the drive folder.

--folder_id : the google drive folder id

--bucket : the name  of the bucket where files will be landed

[optional] --creds_file : if running locally, the path the the service account credentials.json file
```

So an example local invocation of the script would be:
```
python main.py \
    --principal svc_genai-concierge@bostondynamics.com \
    --folder_id 11wtvASfuHoLKkLr_Z_rj85BXgu80MR_V \
    --bucket bd-drive-data \
    --creds_file ./credentials.json
```