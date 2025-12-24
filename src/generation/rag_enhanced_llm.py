"""RAG-enhanced LLM using OpenAI API with learned context."""

from typing import Dict, List, Optional
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI
from src.common.logger import get_logger
from src.common.llm_utils import create_llm_with_fallback
from src.retrieval.file_based_retrieval import FileBasedRetrieval


class RAGEnhancedLLM:
    """LLM enhanced with RAG context for better responses."""
    
    def __init__(self, summaries_dir: str, config: Dict):
        """
        Initialize RAG-enhanced LLM.
        
        Args:
            summaries_dir: Directory containing by_file JSON summaries
            config: Configuration dictionary
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize file-based retrieval for context
        self.retrieval = FileBasedRetrieval(summaries_dir)
        
        # Initialize LLM
        llm_config = config.get("generation", {}).get("llm", {})
        self.llm = create_llm_with_fallback(
            primary_model=llm_config.get("model", "gpt-5-nano"),
            temperature=llm_config.get("temperature", 0.2),
            max_tokens=llm_config.get("max_tokens", 4000),
        )
        
        # Enhanced system prompt with RAG context awareness
        self.system_prompt = """당신은 RFP(제안요청서) 문서 분석 및 제안서 작성 전문가입니다.

당신의 역할:
1. 제공된 RFP 문서 컨텍스트를 정확하게 분석하고 이해합니다.
2. 사용자의 요구사항에 맞는 전문적이고 상세한 제안서를 작성합니다.
3. RFP 문서의 모든 중요한 정보를 반영하여 완성도 높은 제안서를 생성합니다.

작성 규칙:
- 반드시 제공된 컨텍스트만을 기반으로 작성하세요.
- 각 섹션은 최소 3-5문단으로 상세하게 작성하세요.
- 구체적인 수치, 일정, 기술 사양 등은 컨텍스트에서 정확히 인용하세요.
- 한국어로 자연스럽고 전문적으로 작성하세요.
- 최소 2000자 이상의 상세한 내용을 포함하세요.

제안서 구조:
1. 사업 이해 및 배경
2. 제안 개요
3. 기술 제안
4. 사업 수행 계획
5. 조직 및 인력 구성
6. 예산 및 제안 금액
7. 기대 효과 및 성과
8. 차별화 포인트
"""
    
    def generate_with_rag_context(
        self,
        query: str,
        doc_id: Optional[str] = None,
        top_k: int = 5,
        task_type: str = "proposal",  # "proposal", "qa", "summary"
        additional_context: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        previous_output: Optional[str] = None
    ) -> Dict:
        """
        Generate response using RAG context.
        
        Args:
            query: User query or topic
            doc_id: Optional specific document ID
            top_k: Number of chunks to retrieve
            task_type: Type of task ("proposal", "qa", "summary")
            additional_context: Additional context to include
            conversation_history: Previous conversation
            previous_output: Previous generated output (for refinement)
        
        Returns:
            Generated response with metadata
        """
        # Retrieve relevant context
        # If doc_id is provided, search in specific file
        # Otherwise, search across all files using query keywords
        if doc_id:
            chunks = self.retrieval.search_in_file(doc_id, query, top_k=top_k)
        else:
            # Search across all files - will find documents matching query keywords
            # e.g., "도시 사업" will find documents related to "도시" and "사업"
            # If exact match not found, will try fallback with partial keywords
            chunks = self.retrieval.search_across_files(query, top_k=top_k, fallback_search=True)
        
        # If still no chunks found, try to generate based on general knowledge
        use_general_knowledge = False
        if not chunks:
            self.logger.warning(f"No documents found for query: '{query}'. Will generate based on general RFP knowledge.")
            use_general_knowledge = True
            # Create a minimal context based on query keywords
            chunks = []
        
        # Build rich context from chunks
        context_parts = []
        sources = []
        
        if use_general_knowledge:
            # No specific documents found - create general context from query
            query_keywords = query.split()
            context_parts.append(f"""요청된 사업 유형: {query}

참고: '{query}'와 정확히 일치하는 RFP 문서를 찾지 못했습니다.
하지만 유사한 RFP 문서들의 일반적인 패턴과 구조를 기반으로 제안서를 작성하겠습니다.

일반적인 RFP 제안서 구조와 요구사항을 반영하여 작성합니다.""")
        else:
            # Group chunks by document to show multiple documents if found
            docs_found = {}
            for chunk in chunks:
                doc_id_chunk = chunk.get("doc_id", "unknown")
                if doc_id_chunk not in docs_found:
                    docs_found[doc_id_chunk] = {
                        "metadata": chunk.get("metadata", {}),
                        "file_name": chunk.get("file_name", ""),
                        "chunks": []
                    }
                docs_found[doc_id_chunk]["chunks"].append(chunk)
            
            # Add RFP metadata for each document found
            for doc_id_chunk, doc_info in docs_found.items():
                metadata = doc_info["metadata"]
                file_name = doc_info["file_name"]
                metadata_summary = f"""RFP 문서: {file_name}
- 사업명: {metadata.get('사업명', 'N/A')}
- 공고 번호: {metadata.get('공고 번호', 'N/A')}
- 발주 기관: {metadata.get('발주 기관', 'N/A')}
- 사업 금액: {metadata.get('사업 금액', 'N/A')}
- 입찰 참여 마감일: {metadata.get('입찰 참여 마감일', 'N/A')}
"""
                context_parts.append(metadata_summary)
            
            # Add chunk contents
            for chunk in chunks:
                chunk_text = chunk.get("chunk_text", "")
                file_name = chunk.get("file_name", "")
                chunk_index = chunk.get("chunk_index", 0)
                
                context_parts.append(f"[{file_name} - 섹션 {chunk_index}]\n{chunk_text}")
                sources.append({
                    "file_name": file_name,
                    "chunk_id": chunk.get("chunk_id", ""),
                    "score": chunk.get("score", 0.0),
                })
        
        context = "\n\n".join(context_parts)
        
        # Add additional context if provided
        if additional_context:
            context = f"{context}\n\n[추가 컨텍스트]\n{additional_context}"
        
        # Build prompt based on task type
        if task_type == "proposal":
            user_prompt = self._build_proposal_prompt(
                query=query,
                context=context,
                conversation_history=conversation_history,
                previous_output=previous_output,
                use_general_knowledge=use_general_knowledge
            )
        elif task_type == "qa":
            user_prompt = self._build_qa_prompt(
                question=query,
                context=context
            )
        else:
            user_prompt = self._build_general_prompt(
                query=query,
                context=context
            )
        
        # Generate response
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history[-5:]:  # Last 5 messages
                    messages.insert(-1, {"role": msg["role"], "content": msg["content"]})
            
            response = self.llm.invoke(messages)
            
            # Extract response text
            if hasattr(response, 'content'):
                response_text = response.content
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)
            
            return {
                "response": response_text,
                "sources": sources,
                "doc_id": doc_id,
                "total_chunks_used": len(chunks),
                "context_used": True,
                "query": query,
            }
        
        except Exception as e:
            self.logger.error(f"Failed to generate response: {e}", exc_info=True)
            return {
                "response": f"응답 생성 중 오류가 발생했습니다: {str(e)}",
                "sources": sources,
                "context_used": True,
            }
    
    def _build_proposal_prompt(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None,
        previous_output: Optional[str] = None,
        use_general_knowledge: bool = False
    ) -> str:
        """Build prompt for proposal generation."""
        if use_general_knowledge:
            prompt_parts = [
                f"'{query}'에 대한 RFP 제안서를 작성하세요.",
                "",
                "참고 정보:",
                context,
                "",
                "위 정보를 참고하여, 일반적인 RFP 제안서 구조와 '{query}' 사업의 특성을 반영한 제안서를 작성하세요.",
                "실제 RFP 문서가 없더라도, 해당 사업 유형의 일반적인 요구사항과 구조를 기반으로 전문적인 제안서를 작성하세요.",
            ]
        else:
            prompt_parts = [
                "다음 RFP 문서를 분석하여 제안서를 작성하세요.",
                "",
                "RFP 문서 컨텍스트:",
                context,
            ]
        
        if previous_output:
            prompt_parts.extend([
                "",
                "이전 제안서:",
                previous_output[:2000] + "..." if len(previous_output) > 2000 else previous_output,
                "",
                "위 이전 제안서를 기반으로 개선하고 업데이트하세요."
            ])
        
        if conversation_history:
            conv_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in conversation_history[-3:]  # Last 3 messages
            ])
            prompt_parts.extend([
                "",
                "이전 대화:",
                conv_text,
            ])
        
        prompt_parts.extend([
            "",
            "8개 섹션으로 상세한 제안서를 작성하세요 (각 섹션 3-5문단, 최소 2000자):",
            "1. 사업 이해 및 배경",
            "2. 제안 개요",
            "3. 기술 제안",
            "4. 사업 수행 계획",
            "5. 조직 및 인력 구성",
            "6. 예산 및 제안 금액",
            "7. 기대 효과 및 성과",
            "8. 차별화 포인트",
            "",
            "지금 바로 상세한 제안서를 작성하세요:"
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_qa_prompt(self, question: str, context: str) -> str:
        """Build prompt for Q&A."""
        return f"""다음은 RFP 문서의 관련 부분입니다:

{context}

사용자 질문: {question}

위 컨텍스트를 기반으로 질문에 정확하게 답변하세요. 답변 끝에 출처를 명시하세요."""
    
    def _build_general_prompt(self, query: str, context: str) -> str:
        """Build prompt for general tasks."""
        return f"""다음 RFP 문서 컨텍스트를 기반으로 요청사항을 처리하세요:

{context}

요청사항: {query}

위 컨텍스트를 활용하여 요청사항에 맞게 응답하세요."""

