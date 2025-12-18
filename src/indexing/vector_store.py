from typing import List, Any
import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

class VectorStoreWrapper:
    def __init__(self, config: dict):
        self.config = config
        self.collection_name = config.get("vector_db", {}).get("collection_name", "default_collection")
        self.persist_dir = config.get("vector_db", {}).get("persist_directory", "./data/index")
        self.client = None
        self.vector_store = None

    def initialize(self, embedding_function: Any = None):
        """
        Initialize the vector store client (Chroma)
        """
        db_type = self.config.get("vector_db", {}).get("type", "chroma")
        print(f"Initializing {db_type} vector store at {self.persist_dir}...")
        
        # Default to OpenAI Embeddings if not provided
        if embedding_function is None:
            model_name = self.config.get("model", {}).get("embedding_name", "text-embedding-3-small")
            # Assumes OPENAI_API_KEY is in env
            embedding_function = OpenAIEmbeddings(model=model_name)

        if db_type == "chroma":
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=embedding_function,
                persist_directory=self.persist_dir
            )
        else:
            # Fallback or other DBs
            print(f"Warning: Unsupported DB type {db_type}, defaulting to mock/Chroma")
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=embedding_function,
                persist_directory=self.persist_dir
            )

    def add_documents(self, documents: List[Any]):
        """
        Add documents to the vector store.
        documents: List of LangChain Document objects or similar
        """
        if self.vector_store:
            print(f"Adding {len(documents)} chunks to vector store...")
            # Chroma expects a list of Document objects with page_content and metadata
            # Our custom Document class might need conversion if typical LangChain interfaces are strict,
            # but usually duck typing works if attributes match. 
            # Let's ensure they are compatible.
            self.vector_store.add_documents(documents)
            print("Documents added successfully.")
        else:
            print("Vector store not initialized.")

    def similarity_search(self, query: str, k: int = 5):
        print(f"Searching for: {query}")
        if self.vector_store:
            return self.vector_store.similarity_search(query, k=k)
        return []
