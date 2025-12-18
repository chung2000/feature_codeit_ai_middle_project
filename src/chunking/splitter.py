from typing import List
# from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class TextSplitter:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # self.splitter = RecursiveCharacterTextSplitter(
        #     chunk_size=chunk_size,
        #     chunk_overlap=chunk_overlap
        # )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split a list of Documents into smaller chunks.
        """
        print(f"Splitting {len(documents)} documents with size={self.chunk_size}, overlap={self.chunk_overlap}")
        
        # Placeholder logic
        chunked_docs = []
        for doc in documents:
            # Simple mock split
            content = doc.page_content
            # In real implementation: chunks = self.splitter.split_text(content)
            # Here we just treat the whole doc as one chunk for the skeleton
            chunked_docs.append(doc)
            
        return chunked_docs
