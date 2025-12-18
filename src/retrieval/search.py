from typing import List, Dict, Any
from src.indexing.vector_store import VectorStoreWrapper

from src.retrieval.hybrid import get_hybrid_retriever

class Retriever:
    def __init__(self, vector_store: VectorStoreWrapper, k: int = 4):
        self.vector_store = vector_store
        self.hybrid_retriever = get_hybrid_retriever(
            vector_store=vector_store.vector_store,
            k=k
        )

    def retrieve(self, query: str, top_k: int = 5) -> List[Any]:
        """
        Retrieve relevant documents for a query.
        Note: top_k usually fixed at init for Ensemble, but we returns what we get.
        """
        print(f"Retrieving documents (Hybrid) for query: '{query}'")
        return self.hybrid_retriever.invoke(query)

    def retrieve_with_filter(self, query: str, filters: Dict[str, Any], top_k: int = 5) -> List[Any]:
        # TODO: Implement filtering logic
        pass
