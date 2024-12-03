# DOCX to PDF Conversion Service

This is a service which leverages LibreOffice to convert DOCX files to PDF. It expects a DOCX file stored in a GCS location, and writes out the PDF to a specified location in GCS.

## Request Model

As shown in `models.py`, the request model is:
```
{
    "source_uri": <GCS URI of source file>,
    "destination_uri" <GCS URI where PDF output should be written>
}
```

The FastAPI endpoint accepts a list of the above request model. If conversion occurs successfully, the service simply returns a 200 response.