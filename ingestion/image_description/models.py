from pydantic import BaseModel 

class ImageDescriptionRequest(BaseModel):
    source_uri: str
    target_folder_uri: str