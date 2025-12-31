import streamlit as st
import os
import sys
import time

# [SQLite 호환성 패치]
try:
    import pysqlite3
    if not hasattr(pysqlite3, "sqlite_version_info"):
        pysqlite3.sqlite_version_info = (3, 35, 0)
    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    pass

# 설정 파일 로더
try:
    from src.common.config import config
except:
    config = {}

from src.indexing.vector_store import VectorStoreWrapper
from src.generation.rag import RAGChain

st.set_page_config(page_title="RAG ChatBot", page_icon="🤖", layout="wide")

# --- [핵심] DB 로딩 함수 ---
@st.cache_resource
def load_vector_store(embedding_model_name):
    """
    선택된 임베딩 모델("bge-m3" or "kure-v1")에 맞는 DB를 로드합니다.
    """
    db_paths = {
        "bge-m3": "./rfp_database_bge",
        "kure-v1": "./rfp_database_kure"
    }
    target_path = db_paths.get(embedding_model_name)
    
    temp_config = config.copy()
    temp_config["vector_db_path"] = target_path
    temp_config["embedding_model"] = embedding_model_name
    
    wrapper = VectorStoreWrapper(temp_config)
    wrapper.initialize()
    return wrapper

def reset_selected_docs():
    st.session_state.selected_docs = []  # 문서 선택 초기화
    st.toast("🔄 검색 엔진이 변경되어 문서 선택이 초기화되었습니다.", icon="✨")

# --- 사이드바 UI (상단 설정) ---
with st.sidebar:
    st.header("🔧 시스템 설정")
    
    # 1. 임베딩 모델 (DB) 선택
    st.subheader("🧠 검색 엔진 (Embedding)")
    selected_embedding = st.radio(
        "사용할 임베딩 모델",
        ["bge-m3", "kure-v1"],
        index=0,
        help="bge-m3: 다국어 범용 (기본)\nkure-v1: 한국어 특화 (경량)",
        on_change=reset_selected_docs
    )
    
    st.divider()
    
    # 2. 답변 모델 (LLM) 선택
    st.subheader("🤖 답변 AI (LLM)")
    selected_llm = st.selectbox(
        "사용할 언어 모델",
        ["gemma3:12b", "llama3.1"],
        index=0,
        help="Gemma3: 정확도 중시\nLlama3.1: 속도 중시"
    )

    st.divider()


# --- 시스템 로딩 및 하단 사이드바 UI ---
try:
    vector_store_wrapper = load_vector_store(selected_embedding)
    all_docs = vector_store_wrapper.get_all_documents()
    
    with st.sidebar:
        st.subheader("📂 문서 필터")
        
        # session_state에 값이 없으면 미리 빈 리스트로 초기화해줍니다.
        if "selected_docs" not in st.session_state:
            st.session_state.selected_docs = []
            
        selected_docs = st.multiselect(
            "분석 대상 문서",
            options=all_docs,
            key="selected_docs"
        )
        
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
            
        # 시스템 상태 정보 고정 
        st.markdown("---")
        st.success(
            f"🔋 **Current System**\n\n"
            f"🧠 Emb: **{selected_embedding}**\n"
            f"🤖 LLM: **{selected_llm}**"
        )

except Exception as e:
    st.error(f"🚨 DB 로딩 실패! 폴더가 있는지 확인하세요.\n에러: {e}")
    st.stop()


# --- RAG 체인 구성 ---
current_settings = f"{selected_embedding}_{selected_llm}"

if "rag_chain" not in st.session_state or st.session_state.get("current_settings") != current_settings:
    with st.spinner(f"⚙️ 엔진 교체 중... (DB: {selected_embedding} / LLM: {selected_llm})"):
        st.session_state.rag_chain = RAGChain(
            config, 
            vector_store_wrapper, 
            model_name=selected_llm
        )
        st.session_state.current_settings = current_settings
    st.toast(f"✅ 시스템 설정 변경 완료!", icon="🔄")


# --- 메인 화면 ---

if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 기록이 없을 때만(0개일 때만) 타이틀과 가이드 표시
if len(st.session_state.messages) == 0:
    st.title("🤖 AI RFP 분석기")
    
    # 사용 가이드라인
    st.info("""
    **👋 환영합니다! 이렇게 사용해 보세요:**
    
    1. 왼쪽 사이드바에서 [📂 문서 필터]를 눌러 분석할 문서를 선택하세요.
    2. 아래 입력창에 궁금한 점을 물어보세요.
    
    > **(예시)** *"이 사업의 예산은 얼마야?", "제안서 제출 마감일은 언제야?"*
    """)

# 대화 기록 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "latency" in msg:
            st.caption(f"⏱️ 소요 시간: {msg['latency']:.2f}초")
        if "sources" in msg and msg["sources"]:
            with st.expander("📚 분석에 사용된 문서"):
                for src in msg["sources"]:
                    st.markdown(f"- **{src['source']}**: {src['content'][:100]}...")

# 질문 처리
if prompt := st.chat_input("AI RFP 분석기에게 물어보기"):
    # 사용자가 질문을 입력하는 순간, messages 리스트에 추가되므로
    # 다음 리런(Rerun) 때는 위쪽의 타이틀과 가이드가 사라집니다.
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🔍 분석 중..."):
            start_time = time.time()
            
            answer, docs = st.session_state.rag_chain.generate_answer(prompt, selected_docs)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            st.markdown(answer)
            st.caption(f"⏱️ 소요 시간: {elapsed_time:.2f}초")
            
            sources = []
            if docs:
                sources = [{"source": os.path.basename(d.metadata.get('source', 'Unknown')), "content": d.page_content} for d in docs]
                with st.expander("📚 분석에 사용된 문서"):
                    for s in sources:
                        st.markdown(f"- **{s['source']}**: {s['content'][:200]}...")

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources,
                "latency": elapsed_time
            })
