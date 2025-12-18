from typing import List, Optional
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    
class DocumentSource(BaseModel):
    content: str
    metadata: dict
    
class QueryResponse(BaseModel):
    answer: str
    sources: List[DocumentSource]
