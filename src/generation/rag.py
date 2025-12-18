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
        # Fix: Use retrieval.top_k from config (default 3)
        k = config.get("retrieval.top_k", 3)
        self.base_retriever = get_hybrid_retriever(
            vector_store=self.vector_store_wrapper.vector_store,
            k=k
        )
        
        # Default retriever is the base one
        self.retriever = self.base_retriever

        # Re-ranking using FlashRank (Optional)
        self.reranker_retriever = None
        if config.get("retrieval.use_reranker", True):
            compressor = FlashrankRerank()
            self.reranker_retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=self.base_retriever
            )
            # Default to reranker if enabled
            self.retriever = self.reranker_retriever

    def get_retriever(self, fast_mode: bool = False):
        """
        Return the appropriate retriever based on the mode.
        """
        if fast_mode:
            return self.base_retriever
        
        # If fast_mode is False but reranker is not initialized, fallback to base
        return self.reranker_retriever if self.reranker_retriever else self.base_retriever

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
        
        system_prompt = """당신은 제안요청서(RFP) 문서를 분석하는 전문 어시스턴트입니다.
제공된 문맥(Context)에 기반하여 사용자의 질문에 답변하세요.
만약 문맥에서 답을 찾을 수 없다면 "제공된 문서 내용에서 찾을 수 없습니다."라고 답하세요.
답변은 공손하고 전문적인 어조의 한국어로 작성하세요.
중요: 답변은 간결하고 명확하게 작성하세요. 가능하면 핵심 내용을 3~5문장 이내로 요약하십시오. 불필요한 부연 설명은 피하세요.
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

    def stream_answer(self, query: str, context_docs: List[Any], level: str = "보통"):
        """
        Stream the answer generator.
        level: '상세', '보통', '요약', '초요약'
        """
        # Format context (Duplicate logic for now, could be helper)
        if not context_docs:
            context_text = "No relevant context found."
        else:
            context_text = "\n\n".join([f"[Document {i+1}]\n{doc.page_content}" for i, doc in enumerate(context_docs)])
            
        # 레벨별 지시 사항 정의
        level_instructions = {
            "상세": "답변을 매우 구체적이고 상세하게 작성하세요. 문서의 내용을 빠짐없이 설명하고, 필요한 경우 배경 설명도 포함하세요.",
            "보통": "답변을 적절한 길이로 자연스럽게 작성하세요. 핵심 내용과 부가 설명을 균형 있게 포함하세요.",
            "요약": "답변을 간결하게 요약하세요. 핵심 내용 위주로 3~5문장 이내로 작성하세요. 불필요한 설명은 제외하세요.",
            "초요약": "답변을 극도로 짧게 요약하세요. 가장 중요한 핵심 결론만 1~2문장(100자 이내)으로 작성하세요."
        }
        
        instruction = level_instructions.get(level, level_instructions["보통"])

        system_prompt = f"""당신은 제안요청서(RFP) 문서를 분석하는 전문 어시스턴트입니다.
제공된 문맥(Context)에 기반하여 사용자의 질문에 답변하세요.
만약 문맥에서 답을 찾을 수 없다면 "제공된 문서 내용에서 찾을 수 없습니다."라고 답하세요.
답변은 공손하고 전문적인 어조의 한국어로 작성하세요.
중요: {instruction}
"""
        user_prompt = f"""Context:
{context_text}

Question:
{query}

Answer:"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Stream the response
        try:
            for chunk in self.llm.stream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            yield f"Error generating answer: {e}"
