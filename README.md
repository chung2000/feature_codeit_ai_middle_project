# RAG ChatBot (Bid Mate Project)

RFP(제안요청서) 문서를 분석하고 질의응답을 수행하는 **검색 증강 생성(RAG) 기반 챗봇 시스템**입니다.
Python(FastAPI) 백엔드와 Next.js 프론트엔드로 구성되어 있으며, HWP 문서 파싱, Hybrid Search, Re-ranking 등의 고급 검색 기술이 적용되었습니다.

## 1. 프로젝트 개요 (Overview)
- **목적**: 방대한 입찰 공고(RFP) 문서에서 사용자가 원하는 정보(예산, 기간, 자격요건 등)를 신속하게 찾고 요약 제공.
- **주요 기능**:
  - HWP/PDF 문서 자동 텍스트 추출
  - 의미 기반 검색(Vector) + 키워드 검색(BM25) 결합
  - 검색 결과 재순위화(Re-ranking)를 통한 정확도 향상
  - 웹 기반 채팅 인터페이스 제공

## 2. 폴더 구조 (Project Structure)
```
/codeit_ai_middle_project
├── config/              # 설정 파일 (local.yaml 등)
├── data/                # 데이터 저장소
│   ├── files/           # 원본 문서 (PDF, HWP)
│   ├── index/           # ChromaDB 벡터 인덱스
│   └── eval_results.json # 평가 결과
├── src/                 # 백엔드 핵심 소스코드
│   ├── api/             # FastAPI 서버 및 스키마
│   ├── generation/      # RAG 체인 및 LLM 연동
│   ├── indexing/        # 벡터 저장소 관리
│   ├── ingest/          # 문서 로더 및 메타데이터 추출
│   └── retrieval/       # 검색기 (Hybrid, Re-ranking)
├── entrypoint/          # 실행 스크립트 (학습, 추론, 평가)
├── web/                 # 프론트엔드 (Next.js 프로젝트)
├── study_guide.md       # 프로젝트 상세 학습 가이드 (A-Z)
├── requirements.txt     # Python 의존성 패키지
└── Makefile             # 간편 실행 스크립트
```

## 3. 실행 가이드 (Execution Guide)

### 필수 조건
- Python 3.10 이상
- Node.js 18 이상
- OpenAI API Key (`.env` 설정 필수)

### 간편 실행 (Makefile 사용)
프로젝트 루트에서 터미널 2개를 열어 각각 실행합니다.

**터미널 1 (백엔드 서버)**
```bash
make run-backend
# 실행 포트: localhost:8002
```

**터미널 2 (프론트엔드 화면)**
```bash
make run-frontend
# 접속 주소: localhost:3000
```

## 4. 기술 스택 (Tech Stack)

### Backend
- **Language**: Python 3.12
- **Framework**: FastAPI
- **LLM & RAG**: LangChain, OpenAI (GPT-5)
- **Vector DB**: ChromaDB
- **Search**: BM25 + FlashRank (Re-ranking)
- **Parser**: pyhwp (hwp5txt)

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React

## 5. 참고 자료 및 산출물 (References)
- **`study_guide.md`**: 프로젝트 개발 과정과 기술적 의사결정을 담은 상세 문서.
- **`walkthrough.md`**: 상세한 기능 시연 및 검증 리포트.
- **`implementation_plan.md`**: 개발 계획서.

## 6. 라이센스 (License)
MIT License