from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama

class RAGChain:
    def __init__(self, config, vector_store_wrapper, model_name="gemma3:12b"):
        self.config = config
        self.vector_store_wrapper = vector_store_wrapper
        self.model_name = model_name
        
        # 1. 검색기(Retriever) 설정 
        self.retriever = self.vector_store_wrapper.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 8} 
        )

        # 2. LLM 설정
        self.llm = ChatOllama(model=self.model_name, temperature=0)

        # 3. 프롬프트 템플릿
        self.prompt = ChatPromptTemplate.from_template("""
        당신은 RFP(제안요청서) 분석 전문가입니다.
        아래 [Context]에 있는 문서 내용만을 바탕으로 질문에 대해 정확하고 구체적으로 답변하세요.
        문서에 없는 내용은 지어내지 말고 "문서에서 정보를 찾을 수 없습니다"라고 답하세요.
        
        답변 끝에는 반드시 참고한 문서의 출처나 섹션명을 괄호() 안에 명시해주세요.
        예: (문서의 "사업개요" 부분 참조)

        [Context]
        {context}

        [Question]
        {question}

        [Answer]
        """)

        # 4. 체인 구성
        self.chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def generate_answer(self, question, selected_docs=[]):
        """
        질문에 대한 답변과 참고 문서를 반환합니다.
        selected_docs 필터가 있으면 해당 문서 내에서만 검색합니다.
        """
        
        # 문서 필터링 적용 (search_kwargs 동적 수정)
        search_kwargs = {"k": 8}
        if selected_docs:
            # metadata의 'source' 필드에 파일명이 포함되는지 확인 (ChromaDB 문법)
            # 여기서는 간단하게 $in 연산자나 $or 연산자를 활용할 수 있으나,
            # Chroma 버전에 따라 다르므로 단순하게 파일명 필터링을 시도합니다.
            
            # (주의) Chroma에서 복잡한 필터는 where 절을 사용해야 합니다.
            # 여기서는 사용자가 선택한 파일명 목록(selected_docs) 중 하나라도 일치하면 가져오도록 합니다.
            # 파일 경로가 전체 경로일 수 있으므로, 파일명만 추출해서 비교하는게 안전하지만
            # 일단 selected_docs에 들어있는 값 그대로 필터링을 시도합니다.
            
            if len(selected_docs) == 1:
                search_kwargs["filter"] = {"source": selected_docs[0]}
            else:
                # 2개 이상일 때는 $or 연산자 사용
                search_kwargs["filter"] = {
                    "$or": [{"source": doc} for doc in selected_docs]
                }
        
        # 리트리버 업데이트
        self.retriever.search_kwargs = search_kwargs
        
        # 1. 문서 검색 (Retrieve)
        retrieved_docs = self.retriever.invoke(question)
        
        # 2. 답변 생성 (Generate)
        # context를 포맷팅해서 문자열로 만듦
        context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        # chain.invoke에 딕셔너리가 아닌 문자열 등을 넘길 수도 있지만,
        # 위에서 정의한 chain 구조상 invoke(question)을 하면 
        # {"context": retriever...} 부분이 작동해야 하는데, 
        # 여기서는 우리가 직접 context를 뽑았으므로, 프롬프트+LLM 부분만 따로 실행하거나
        # 체인 구조를 그대로 둡니다.
        
        # 가장 깔끔한 방법: 체인 전체 실행
        answer = self.chain.invoke(question)
        
        return answer, retrieved_docs
