import streamlit as st
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. 설정 로드
load_dotenv()
st.set_page_config(page_title="RFP 검색기", page_icon="🔍")
DB_PATH = "./rfp_database"

# 2. 제목 및 설명
st.title("🤖 AI RFP 분석기")
st.caption("문서 내용을 근거로 답변하고, 참고한 원문까지 보여줍니다.")

# --- [추가] 사이드바: DB에서 파일 목록 가져와서 보여주기 ---
st.sidebar.header("📂 문서 선택")

# DB에 어떤 파일들이 있는지 확인하는 함수
def get_file_list():
    if os.path.exists(DB_PATH):
        # DB를 잠시 열어서 메타데이터만 확인
        _embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        _db = Chroma(persist_directory=DB_PATH, embedding_function=_embeddings)
        data = _db.get()
        # 저장된 모든 문서의 경로(source)를 가져와서 중복 제거
        return list(set([m['source'] for m in data['metadatas']]))
    return []

# 파일 목록 로드
all_files = get_file_list()
# {파일명: 전체경로} 형태로 짝꿍 만들기
file_map = {os.path.basename(f): f for f in all_files}

# 선택 박스 만들기
selected_file = st.sidebar.selectbox(
    "검색할 문서를 선택하세요:",
    ["전체 문서 검색"] + list(file_map.keys())
)

# 3. 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "안녕하세요! RFP 문서에 대해 무엇이든 물어보세요."}]

# 4. 채팅 기록 표시
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 5. 사용자 입력 처리
if prompt := st.chat_input("질문을 입력하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # --- [RAG 로직 시작] ---
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    if os.path.exists(DB_PATH):
        vectordb = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
        
        # --- [추가] 선택한 파일만 보게 하는 필터링 로직 ---
        search_kwargs = {"k": 7} # 기본은 3개 검색
        
        if selected_file != "전체 문서 검색":
            # 사용자가 파일을 선택했다면, 그 파일 경로(source)랑 똑같은 것만 찾으라고 명령
            target_path = file_map[selected_file]
            search_kwargs["filter"] = {"source": target_path}
            st.toast(f"🔒 '{selected_file}' 문서 안에서만 찾습니다.")
            
        # 필터가 적용된 검색기 생성
        retriever = vectordb.as_retriever(search_kwargs=search_kwargs) 
        
        # ... (이 아래 retrieved_docs = retriever.invoke(prompt) 부터는 그대로 둠) ...
        # [단계 1] 문서를 먼저 검색해 옵니다 (Retriever 실행)
        with st.spinner("관련 문서를 찾는 중..."):
            retrieved_docs = retriever.invoke(prompt)
        
        # 문서 내용을 문자열로 합치기
        def format_docs(docs):
            return "\n\n".join([d.page_content for d in docs])
            
        context_text = format_docs(retrieved_docs)

        # [단계 2] 이전 대화 기록 가져오기
        chat_history_str = ""
        for msg in st.session_state.messages[:-1]:
            role = "Human" if msg["role"] == "user" else "AI"
            chat_history_str += f"{role}: {msg['content']}\n"

        # [단계 3] 프롬프트 및 답변 생성
        template = """
        당신은 제안요청서(RFP) 분석 전문가입니다. 
        아래 [참고 문서]만을 근거로 사용하여 질문에 답변하세요.
        문서에 없는 내용은 "문서에 나와있지 않습니다"라고 솔직히 말하세요.
        
        [이전 대화 기록]:
        {chat_history}

        [참고 문서]: 
        {context}
        
        질문: {question}
        """
        rag_prompt = ChatPromptTemplate.from_template(template)
        
        # 모델 설정
        model = ChatOpenAI(model="gpt-5-mini", temperature=0)
        
        chain = rag_prompt | model | StrOutputParser()
        
        with st.chat_message("assistant"):
            # 답변 출력
            with st.spinner("분석 결과를 작성 중..."):
                response = chain.invoke({
                    "context": context_text,
                    "question": prompt,
                    "chat_history": chat_history_str
                })
                st.write(response)
            
            # [핵심 기능 추가] 참고한 문서 원문 보여주기
            with st.expander("📚 참고한 문서 원문 보기 (클릭)"):
                for i, doc in enumerate(retrieved_docs):
                    source = doc.metadata.get('source', '알 수 없음').split('/')[-1]
                    st.markdown(f"**📖 참고 문서 {i+1}: {source}**")
                    st.info(doc.page_content[:300] + "...") # 너무 기니까 300자만 미리보기
        
        # 기록 저장
        st.session_state.messages.append({"role": "assistant", "content": response})
        
    else:
        st.error("데이터베이스가 없습니다. 먼저 문서를 임베딩해주세요.")

# 가상환경 켜기: source ~/myenv/bin/activate
# 실행문(터미널에 입력): streamlit run entrypoint/app.py