import os
import glob
import re
import olefile
import zlib
import struct
import fitz  # PyMuPDF
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# --- [설정] 만들 DB 목록 ---
TARGET_DBS = [
    {"name": "bge-m3",  "path": "./rfp_database_bge"},
    {"name": "kure-v1", "path": "./rfp_database_kure"}
]

load_dotenv()
DATA_DIR = "./data/01-raw"

# --- [전처리 함수] ---
def clean_text(text):
    """
    노이즈 제거: 
    1.  (Unit Separator), 수직 탭, 폼 피드 등 화면에 이상하게 찍히는 제어 문자를 제거합니다.
    2. 필요한 한글/영어/숫자/기호는 그대로 살립니다.
    """
    # 특수문자(=\x1f) 및 제어 문자 강력 제거
    text = text.replace("\x1f", " ").replace("\x0b", " ").replace("\x0c", " ")
    text = re.sub(r'[\x00-\x08\x0e-\x1f\x7f]', ' ', text)
    
    # 기존 허용 패턴 유지
    pattern = r"[^가-힣a-zA-Z0-9\s\.,\-\(\)\[\]\%\~\'\"·]"
    text = re.sub(pattern, " ", text)
    
    # 공백 정리
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

# --- [HWP 추출 함수] ---
def get_hwp_text(filename):
    try:
        f = olefile.OleFileIO(filename)
        dirs = f.listdir()
        
        if not any(d[0] == "BodyText" for d in dirs): return ""
        
        nums = []
        for d in dirs:
            if d[0] == "BodyText":
                try: nums.append(int(d[1].replace("Section", "")))
                except: pass
        nums.sort()
        
        header = f.openstream("FileHeader")
        is_compressed = (header.read()[36] & 1) == 1
        
        text = ""
        for i in nums:
            b_data = f.openstream(f"BodyText/Section{i}").read()
            if is_compressed: b_data = zlib.decompress(b_data, -15)
            
            i = 0
            while i < len(b_data):
                header = struct.unpack_from("<I", b_data, i)[0]
                rec_len = (header >> 20) & 0xfff
                if (header & 0x3ff) == 67:
                    rec_payload = b_data[i+4:i+4+rec_len]
                    text += rec_payload.decode('utf-16-le', errors='ignore') + "\n"
                i += 4 + rec_len
        return clean_text(text)
    except Exception as e:
        print(f"⚠️ HWP 읽기 에러({os.path.basename(filename)}): {e}")
        return ""

# --- [PDF 추출 함수] ---
def get_pdf_text(filename):
    text = ""
    try:
        doc = fitz.open(filename)
        for page in doc:
            text += page.get_text(sort=True) + "\n"
        doc.close()
        return clean_text(text)
    except:
        return ""

# --- [메인 실행] ---
if __name__ == "__main__":
    print(f"🚀 [최종 DB 생성기] 데이터 로딩 시작: {DATA_DIR}")
    
    docs = []
    files = glob.glob(os.path.join(DATA_DIR, "*.*"))

    for f in files:
        filename = os.path.basename(f)
        ext = f.split('.')[-1].lower()
        content = ""
        
        if ext == 'hwp':
            content = get_hwp_text(f)
            if "벤처" in filename:
                print(f"👀 [확인] {filename} 읽기 성공! (길이: {len(content)})")
                if "352,000,000" in content:
                    print("   -> ✅ 핵심 데이터(352,000,000) 포함됨!")
        elif ext == 'pdf':
            content = get_pdf_text(f)
        else:
            continue
            
        if content:
            # 파일명만 저장 (필터링 오류 방지)
            docs.append(Document(page_content=content, metadata={"source": filename}))

    if not docs:
        print("❌ 로드된 문서가 없습니다.")
        exit()

    print(f"\n총 {len(docs)}개 문서 로드 완료. 청킹 시작...")

    # [핵심 수정] kure-v1을 위해 600자로 안전하게 축소! (Overlap 100)
    # 이제 kure-v1이 소화불량에 걸리지 않고 모든 텍스트를 꼼꼼히 씹어먹을 수 있습니다.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600, 
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_documents(docs)

    print("\n-------------------------------------------------")
    for db_info in TARGET_DBS:
        model_name = db_info["name"]
        db_path = db_info["path"]
        
        print(f"🔥 {model_name} DB 생성 중... ({db_path})")
        try:
            embeddings = OllamaEmbeddings(model=model_name)
            import shutil
            if os.path.exists(db_path):
                shutil.rmtree(db_path)
            
            Chroma.from_documents(chunks, embeddings, persist_directory=db_path)
            print(f"✅ {model_name} 완료!")
        except Exception as e:
            print(f"❌ 실패: {e}")
        print("-------------------------------------------------")
          
# 기존 DB 삭제
# 터미널에: rm -rf rfp_database_bge rfp_database_kure
# 가상환경 켜기: source .venv/bin/activate  