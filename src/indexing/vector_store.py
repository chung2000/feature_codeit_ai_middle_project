from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

class VectorStoreWrapper:
    def __init__(self, config):
        self.config = config
        self.vector_store = None
        
        self.persist_directory = config.get("vector_db_path", "./rfp_database_bge")
        self.embedding_model_name = config.get("embedding_model", "bge-m3")

    def initialize(self):
        print(f"📂 DB 로딩 시작: {self.persist_directory} (Model: {self.embedding_model_name})")
        
        # 동적으로 모델명 할당
        self.embedding = OllamaEmbeddings(model=self.embedding_model_name)
        
        self.vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding
        )
        print("✅ DB 로딩 완료!")

    def get_all_documents(self):
        if not self.vector_store:
            return []
        # 메타데이터에서 source만 추출해서 중복 제거 후 반환
        data = self.vector_store.get()
        sources = set([meta.get('source').split('/')[-1] for meta in data['metadatas']])
        return list(sources)
