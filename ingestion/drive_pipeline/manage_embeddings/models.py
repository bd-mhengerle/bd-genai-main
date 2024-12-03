from pydantic import BaseModel

class LoadDriveFilesRequest(BaseModel):
    project: str
    bucket: str
    folder_id: str
    index_name: str
    batch_size: int