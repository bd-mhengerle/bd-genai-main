from pydantic import BaseModel

class LoadPineconeRequest(BaseModel):
    bucket_name: str
    index_name: str
    batch_size: int
    cache_freshness: int