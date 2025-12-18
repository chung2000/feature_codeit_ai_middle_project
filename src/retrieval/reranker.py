from typing import Sequence, List
from langchain_core.callbacks import Callbacks
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents.compressor import BaseDocumentCompressor
from flashrank import Ranker, RerankRequest

class FlashrankRerank(BaseDocumentCompressor):
    """
    LangChain BaseDocumentCompressor wrapper for FlashRank.
    """
    model: str = "ms-marco-TinyBERT-L-2-v2"
    ranker: Ranker = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, model: str = "ms-marco-TinyBERT-L-2-v2", **kwargs):
        super().__init__(model=model, **kwargs)
        self.ranker = Ranker(model_name=model)

    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Callbacks = None,
    ) -> Sequence[Document]:
        """
        Rerank documents using FlashRank.
        """
        if not documents:
            return []

        passages = [
            {"id": str(i), "text": doc.page_content, "meta": doc.metadata}
            for i, doc in enumerate(documents)
        ]

        rerank_request = RerankRequest(query=query, passages=passages)
        results = self.ranker.rerank(rerank_request)

        reranked_docs = []
        for res in results:
            doc_idx = int(res["id"])
            original_doc = documents[doc_idx]
            # Update score if needed, or just keep order
            original_doc.metadata["relevance_score"] = res["score"]
            reranked_docs.append(original_doc)

        return reranked_docs
