from typing import List
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_classic.retrievers.ensemble import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.vectorstores import VectorStore

def get_hybrid_retriever(
    vector_store: VectorStore, 
    documents: List[Document] = None, 
    k: int = 4,
    weights: List[float] = [0.5, 0.5]
) -> BaseRetriever:
    """
    Create an EnsembleRetriever combining BM25 (keyword) and VectorStore (semantic).
    
    Args:
        vector_store: The Chroma (or other) vector store instance.
        documents: List of documents to initialize BM25. 
                   If None, attempts to fetch from vector_store if supported.
        k: Number of documents to retrieve for each retriever.
        weights: Weights for [BM25, Vector].
        
    Returns:
        EnsembleRetriever
    """
    
    # 1. Initialize Vector Retriever
    vector_retriever = vector_store.as_retriever(search_kwargs={"k": k})
    
    # 2. Initialize BM25 Retriever
    if not documents:
        # Try to fetch all docs from Chroma if accessible
        # Note: 'get' is specific to Chroma and some others, might vary
        try:
            # Check if it is a Chroma wrapper or actual Chroma object
            # If it's our VectorStoreWrapper, we need to access the internal store
            if hasattr(vector_store, "get"): 
                # This fetches metadata and text, might be heavy if large
                result = vector_store.get() 
                texts = result['documents']
                metadatas = result['metadatas']
                documents = [
                    Document(page_content=t, metadata=m) 
                    for t, m in zip(texts, metadatas) if t # filter None
                ]
            else:
                print("Warning: Could not fetch documents from vector store for BM25. Hybrid search might fail if documents are not provided.")
                return vector_retriever
        except Exception as e:
            print(f"Error fetching documents for BM25: {e}")
            return vector_retriever

    if not documents:
        print("Warning: No documents found for BM25 initialization. Returning vector retriever only.")
        return vector_retriever

    bm25_retriever = BM25Retriever.from_documents(documents)
    bm25_retriever.k = k

    # 3. Create Ensemble
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=weights
    )
    
    return ensemble_retriever
