"""File-based RAG using JSON summaries."""

from typing import Dict, List, Optional
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from src.retrieval.file_based_retrieval import FileBasedRetrieval
from src.common.logger import get_logger
from src.common.llm_utils import create_llm_with_fallback


SYSTEM_PROMPT = """당신은 RFP(제안요청서) 문서 분석 전문가입니다. 
제공된 문서 컨텍스트를 기반으로 사용자의 질문에 정확하고 상세하게 답변하세요.

규칙:
1. 반드시 제공된 컨텍스트만을 기반으로 답변하세요.
2. 컨텍스트에 없는 정보는 추측하지 말고 "문서에 명시되지 않음"이라고 명시하세요.
3. 답변의 출처를 명확히 표시하세요 (파일명, 문서 ID 등).
4. 한국어로 자연스럽고 전문적으로 답변하세요.
"""

USER_PROMPT_TEMPLATE = """다음은 RFP 문서의 관련 부분입니다:

{context}

사용자 질문: {question}

위 컨텍스트를 기반으로 질문에 답변하세요. 답변 끝에 출처를 명시하세요.
"""


class FileBasedRAG:
    """RAG chain using file-based JSON summaries."""
    
    def __init__(self, summaries_dir: str, config: Dict):
        """
        Initialize file-based RAG.
        
        Args:
            summaries_dir: Directory containing by_file JSON summaries
            config: Configuration dictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize file-based retrieval
        self.retrieval = FileBasedRetrieval(summaries_dir)
        
        # Initialize LLM
        llm_config = config.get("generation", {}).get("llm", {})
        self.llm = create_llm_with_fallback(
            primary_model=llm_config.get("model", "gpt-5-nano"),
            temperature=llm_config.get("temperature", 0.2),
            max_tokens=llm_config.get("max_tokens", 2000),
        )
        
        # Create prompt template
        system_template = SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT)
        human_template = HumanMessagePromptTemplate.from_template(USER_PROMPT_TEMPLATE)
        
        self.prompt = ChatPromptTemplate.from_messages([
            system_template,
            human_template
        ])
    
    def answer_question(
        self,
        question: str,
        doc_id: Optional[str] = None,
        top_k: int = 5
    ) -> Dict:
        """
        Answer a question using file-based retrieval.
        
        Args:
            question: User question
            doc_id: Optional specific document ID to search in
            top_k: Number of chunks to retrieve
        
        Returns:
            Dictionary with answer, sources, and metadata
        """
        # Retrieve relevant chunks
        if doc_id:
            # Search in specific file
            chunks = self.retrieval.search_in_file(doc_id, question, top_k=top_k)
        else:
            # Search across all files
            chunks = self.retrieval.search_across_files(question, top_k=top_k)
        
        if not chunks:
            return {
                "answer": "관련 문서를 찾을 수 없습니다.",
                "sources": [],
                "doc_id": doc_id,
                "total_chunks_used": 0,
            }
        
        # Build context from chunks
        context_parts = []
        sources = []
        
        for chunk in chunks:
            chunk_text = chunk.get("chunk_text", "")
            file_name = chunk.get("file_name", "")
            chunk_id = chunk.get("chunk_id", "")
            
            context_parts.append(f"[{file_name} - 청크 {chunk.get('chunk_index', 0)}]\n{chunk_text}")
            sources.append({
                "file_name": file_name,
                "chunk_id": chunk_id,
                "score": chunk.get("score", 0.0),
            })
        
        context = "\n\n".join(context_parts)
        
        # Generate answer using LLM
        try:
            messages = self.prompt.format_messages(
                context=context,
                question=question
            )
            
            response = self.llm.invoke(messages)
            
            # Extract answer text
            if hasattr(response, 'content'):
                answer = response.content
            elif isinstance(response, str):
                answer = response
            else:
                answer = str(response)
            
            return {
                "answer": answer,
                "sources": sources,
                "doc_id": doc_id,
                "total_chunks_used": len(chunks),
                "query": question,
            }
        
        except Exception as e:
            self.logger.error(f"Failed to generate answer: {e}", exc_info=True)
            return {
                "answer": f"답변 생성 중 오류가 발생했습니다: {str(e)}",
                "sources": sources,
                "doc_id": doc_id,
                "total_chunks_used": len(chunks),
            }
    
    def get_file_info(self, doc_id: str) -> Optional[Dict]:
        """
        Get information about a specific file.
        
        Args:
            doc_id: Document ID
        
        Returns:
            File summary information
        """
        summary = self.retrieval.load_file_summary(doc_id)
        if not summary:
            return None
        
        return {
            "doc_id": summary.get("doc_id", ""),
            "file_name": summary.get("file_name", ""),
            "file_type": summary.get("file_type", ""),
            "metadata": summary.get("metadata", {}),
            "chunking_statistics": summary.get("chunking_statistics", {}),
        }
    
    def list_files(self) -> List[Dict]:
        """
        List all available files.
        
        Returns:
            List of file metadata
        """
        return self.retrieval.list_available_files()

