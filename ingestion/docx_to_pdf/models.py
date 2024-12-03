from pydantic import BaseModel

class GCSConversionRequest(BaseModel):
    source_uri: str 
    destination_uri: str 
    