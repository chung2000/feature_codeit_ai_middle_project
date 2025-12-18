from typing import List, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.retrieval.hybrid import get_hybrid_retriever
from src.retrieval.reranker import FlashrankRerank
from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever

class RAGChain:
    def __init__(self, config: dict, vector_store_wrapper):
        self.vector_store_wrapper = vector_store_wrapper
        self.llm_name = config.get("model.llm_name", "gpt-5")
        # Initialize LLM
        # Assumes OPENAI_API_KEY is in environment
        self.llm = ChatOpenAI(model_name=self.llm_name, temperature=0)
        
        # Use Hybrid Retriever (BM25 + Chroma)
        # k defaults to 4 in get_hybrid_retriever, or we can pass config
        k = config.get("retrieval.k", 4)
        self.retriever = get_hybrid_retriever(
            vector_store=self.vector_store_wrapper.vector_store,
            k=k
        )

        # Re-ranking using FlashRank
        if config.get("retrieval.use_reranker", True):
            compressor = FlashrankRerank()
            self.retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=self.retriever
            )

    def generate_answer(self, query: str, context_docs: List[Any]) -> str:
        """
        Generate an answer based on the query and retrieved context.
        """
        # Format context
        if not context_docs:
            context_text = "No relevant context found."
        else:
            # Limit context length loosely to avoid strict token limits for now, 
            # though gpt-4o has large context.
            context_text = "\n\n".join([f"[Document {i+1}]\n{doc.page_content}" for i, doc in enumerate(context_docs)])
        
        system_prompt = """You are a professional assistant for analyzing Request for Proposal (RFP) documents.
Answer the user's question based ONLY on the provided Context.
If the answer is not in the context, say "제공된 문서 내용에서 찾을 수 없습니다."
Provide the answer in Korean, in a polite and professional tone.
"""

        user_prompt = f"""Context:
{context_text}

Question:
{query}

Answer:"""
        
        print(f"Generating answer with model {self.llm_name}...")
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"Error generating answer: {e}"
