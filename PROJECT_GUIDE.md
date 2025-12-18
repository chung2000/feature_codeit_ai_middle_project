# RAG ChatBot 프로젝트 학습 가이드 (Study Guide)

이 문서는 프로젝트가 시작된 시점부터 현재까지의 개발 과정, 아키텍처 결정, 그리고 해결된 기술적 이슈들을 **A부터 Z까지 상세하게 정리한 교육 자료**입니다.

---

## 🏗️ 1단계: 프로젝트 기초 공사 (Phase 0-1)

### 1.1 프로젝트 목표
RFP(제안요청서) 문서를 분석하고 사용자의 질의에 답변하는 **RAG(검색 증강 생성)** 시스템 구축.

### 1.2 아키텍처 설계 (Architecture)
- **Ingestion (데이터 적재)**: PDF/HWP 문서 → 텍스트 추출 → Chunking → Embedding → Vector DB
- **Retrieval (검색)**: 사용자 질문 → Hybrid Search (BM25 + Vector) → Re-ranking
- **Generation (생성)**: 검색된 문서 + 질문 → Prompt → LLM (GPT-5) → 답변

### 1.3 핵심 컴포넌트 구현
1.  **문서 로더 (`src/ingest/loader.py`)**:
    -   초기엔 `olefile`을 썼으나 HWP 추출 품질이 낮아 **`pyhwp (hwp5txt)`** 서브프로세스 방식으로 전환하여 해결.
2.  **벡터 저장소 (`src/indexing`)**:
    -   **ChromaDB**를 사용하여 로컬 파일 기반의 벡터 DB 구축.
    -   임베딩 모델: `text-embedding-3-small` (OpenAI).

---

## ⚙️ 2단계: 시스템 고도화 (Phase 2)

기본적인 검색 기능 구현 후 품질을 높이기 위한 작업을 진행했습니다.

### 2.1 하이브리드 검색 (Hybrid Search)
-   **문제**: 단순 벡터 검색은 키워드 매칭(예: 정확한 예산 금액)에 약함.
-   **해결**: `BM25Retriever`(키워드) + `VectorStoreRetriever`(의미)를 **`EnsembleRetriever`**로 결합.

### 2.2 리랭킹 (Re-ranking)
-   **도구**: `FlashRank` (경량화된 Cross-Encoder).
-   **로직**: 1차 검색에서 10~20개를 가져온 뒤, 질문과의 관련성 점수를 다시 계산하여 상위 3~5개만 LLM에 전달.
-   **효과**: 정확도 대폭 상승.

### 2.3 서빙 API (`src/api/app.py`)
-   **프레임워크**: **FastAPI** 사용.
-   **포트 이슈**: 개발 중 8000, 8001번 포트 충돌이 잦아 **8002번**으로 최종 확정.
-   **Numpy 이슈**: `FlashRank`가 반환하는 점수(`float32`)가 JSON 직렬화가 안 되는 버그 발생 → `clean_metadata` 함수로 해결.

---

## 💻 3단계: 사용자 인터페이스 (Phase 3: Frontend)

개발자만 쓰는 CLI가 아닌, 실제 사용자를 위한 웹 화면을 개발했습니다.

### 3.1 기술 스택
-   **Framework**: **Next.js 14** (App Router).
-   **Styling**: **Tailwind CSS**.
-   **Icons**: `lucide-react`.

### 3.2 주요 기능 (`web/src/components/ChatInterface.tsx`)
-   **채팅 UI**: 카카오톡/ChatGPT 스타일의 대화형 인터페이스.
-   **스트리밍 중단**: 답변 생성 중 `AbortController`를 사용하여 요청을 취소하는 **중단(Stop)** 기능 구현.
-   **출처 표시**: 답변 밑에 "참고 문서" 아코디언을 두어 신뢰성 확보.

### 3.3 연동 (Integration)
-   프론트엔드(`localhost:3000`) ↔ 백엔드(`localhost:8002`) 간 CORS 설정 추가.
-   `Makefile`을 통해 루트 디렉토리에서 한 번에 실행 가능한 환경 구축.

---

## 📊 4단계: 결과 시각화 및 데모 (Notebook)

결과 보고 및 시연을 위해 Jupyter Notebook을 추가했습니다.

### 4.1 데모 노트북 (`notebooks/demo.ipynb`)
- **위치**: `notebooks/demo.ipynb`
- **실행 방법**:
  ```bash
  # 의존성 설치 (requirements.txt에 notebook, ipykernel 포함됨)
  pip install -r requirements.txt
  
  # VS Code 등에서 demo.ipynb 열기 또는 jupyter notebook 실행
  jupyter notebook notebooks/demo.ipynb
  ```
- **주요 내용**:
  1.  **시스템 초기화**: 코드베이스(`src`)를 직접 import하여 RAG 체인 가동.
  2.  **검색 시연**: 질문 입력 시 `Retrieval` -> `Re-ranking` 과정을 거쳐 어떤 문서가 뽑히는지 리스트 출력.
  3.  **답변 생성**: LLM이 생성한 최종 답변 확인.
  4.  **성능 평가**: `eval_results.json` 파일을 그래프/표 (`pandas`)로 시각화하여 수치적 근거 제시.

---

## 📝 개발 중 주요 이슈 및 해결 일지 (Troubleshooting Log)

| 이슈 (Issue) | 원인 (Cause) | 해결 (Resolution) |
| :--- | :--- | :--- |
| **HWP 텍스트 깨짐** | `olefile` 파서의 한계 | `pyhwp`의 `hwp5txt` CLI 도구 연동으로 교체 |
| **포트 충돌 (Address in use)** | 이전 프로세스 잔존 & 기본 포트(8000) 혼잡 | `lsof`/`fuser`로 정리 후 포트를 **8002**로 변경 |
| **JSON 직렬화 오류** | Numpy float32 타입 호환 불가 | Pydantic 응답 생성 전 Python float로 변환 로직 추가 |
| **LLM 모델 권한 오류** | `gpt-4o` 접근 권한 없음 | 프로젝트 승인된 **`gpt-5`** 모델로 변경 |
| **Import Error** | LangChain 버전 파편화 | `langchain_core`, `langchain_community` 등으로 경로 최적화 |

---

## 📚 마무리
이 프로젝트는 단순한 RAG 구현을 넘어, **실제 서비스 가능한 수준의 품질(Re-ranking), 사용성(Web UI), 안정성(Error Handling)**을 갖추는 데 주력했습니다.
이 가이드가 향후 유지보수나 확장에 도움이 되기를 바랍니다.
