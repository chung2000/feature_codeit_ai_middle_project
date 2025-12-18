from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys
import numpy as np

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.common.config import config
from src.indexing.vector_store import VectorStoreWrapper
from src.generation.rag import RAGChain
from src.api.schemas import QueryRequest, QueryResponse, DocumentSource

# Global state
rag_chain = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load RAG Chain
    global rag_chain
    print("Loading RAG System...")
    
    # Initialize Vector Store
    vector_store = VectorStoreWrapper(config)
    vector_store.initialize()
    
    # Initialize RAG Chain
    rag_chain = RAGChain(config=config, vector_store_wrapper=vector_store)
    print("RAG System Ready.")
    
    yield
    
    # Shutdown
    print("Shutting down...")

app = FastAPI(title="RAG ChatBot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    if not rag_chain:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        # Retrieve context
        # We need to access the retriever directly or add a method to RAGChain to get docs
        # RAGChain.generate_answer takes context_docs, but we usually run retrieval inside
        # Let's see how RAGChain is implemented. It currently separates generation.
        # We should probably update RAGChain to have a full `invoke` or `run` method
        # For now, let's manually retrieve here or update RAGChain.
        
        # Manually retrieving for now based on current class design
        retriever = rag_chain.retriever
        docs = retriever.invoke(request.query)
        
        # Generate answer
        answer = rag_chain.generate_answer(request.query, docs)
        
        # Format sources
        def clean_metadata(meta: dict) -> dict:
            cleaned = {}
            for k, v in meta.items():
                if isinstance(v, (np.float32, np.float64)):
                    cleaned[k] = float(v)
                elif isinstance(v, (np.int32, np.int64)):
                    cleaned[k] = int(v)
                else:
                    cleaned[k] = v
            return cleaned

        sources = [
            DocumentSource(content=d.page_content, metadata=clean_metadata(d.metadata))
            for d in docs
        ]
        
        return QueryResponse(answer=answer, sources=sources)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8002, reload=True)
