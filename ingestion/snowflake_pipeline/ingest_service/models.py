from pydantic import BaseModel

class LoadPineconeRequest(BaseModel):
    snowflake_source: str
    batch_size: int
    truncate: bool = False
