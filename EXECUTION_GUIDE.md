# 🚀 실행 가이드 (Execution Guide)

프로젝트 실행 시 참고할 문서입니다.

---

## 📚 참고 문서 목록

### 1. 프로젝트 개요

- **README.md**: 프로젝트 구조 및 목적
- **agent/PRD.md**: 제품 요구사항 문서
- **agent/PLAN.md**: 프로젝트 일정 및 계획

### 2. 에이전트별 구현 가이드

각 에이전트의 상세 구현 프롬프트:

- **agent/INGEST_AGENT.md**: 문서 파싱 및 전처리
- **agent/CHUNKING_AGENT.md**: 텍스트 청킹
- **agent/INDEXING_AGENT.md**: 벡터 임베딩 및 인덱싱
- **agent/RETRIEVAL_AGENT.md**: 검색 및 리랭킹
- **agent/GENERATION_AGENT.md**: 답변 생성 (RAG)
- **agent/EVAL_AGENT.md**: 평가 및 리포트

### 3. 설정 파일

- **config/local.yaml**: 로컬 개발 환경 설정
- **config/prod.yaml**: 프로덕션 환경 설정

---

## 🛠️ 환경 설정

### 1. 의존성 설치

```bash
# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정

**⚠️ 중요**: `OPENAI_API_KEY` 환경변수는 필수입니다!

**자세한 설정 방법**: [ENV_SETUP.md](./ENV_SETUP.md) 참조

**빠른 설정**:

```bash
# Linux/Mac
export OPENAI_API_KEY=sk-your-api-key-here

# 확인
echo $OPENAI_API_KEY
```

또는 `.env` 파일 생성:

```
OPENAI_API_KEY=sk-your-api-key-here
```

그리고 실행 전에:

```bash
export $(cat .env | xargs)
```

### 3. 데이터 준비

- 원본 문서: `data/files/` 디렉토리에 PDF/HWP 파일 배치
- 메타데이터: `data/data_list.csv` 파일 준비

---

## 📋 실행 단계

### Step 1: 문서 수집 및 전처리 (Ingest)

```bash
# 전체 파이프라인 실행
python entrypoint/train.py --config config/local.yaml --step ingest

# 또는 전체 실행
python entrypoint/train.py --config config/local.yaml --step all
```

**참고 문서**: `agent/INGEST_AGENT.md`

**입력**:

- `data/files/`: 원본 PDF/HWP 파일
- `data/data_list.csv`: 메타데이터 CSV

**출력**:

- `data/preprocessed/`: 전처리된 텍스트 파일 (JSON)

**체크리스트**:

- [ ] PDF 파일 파싱 성공
- [ ] HWP 파일 파싱 성공
- [ ] 메타데이터 매핑 확인
- [ ] 전처리 결과 파일 생성 확인

---

### Step 2: 텍스트 청킹 (Chunking)

```bash
python entrypoint/train.py --config config/local.yaml --step chunking
```

**참고 문서**: `agent/CHUNKING_AGENT.md`

**입력**:

- `data/preprocessed/`: 전처리된 텍스트 파일

**출력**:

- `data/features/chunks.jsonl`: 청킹 결과 (JSONL)

**체크리스트**:

- [ ] 청킹 결과 파일 생성
- [ ] 청크 통계 리포트 확인
- [ ] 메타데이터 보존 확인

---

### Step 3: 벡터 인덱싱 (Indexing)

```bash
# OpenAI API 키 필요
export OPENAI_API_KEY=your_key_here
python entrypoint/train.py --config config/local.yaml --step indexing
```

**참고 문서**: `agent/INDEXING_AGENT.md`

**입력**:

- `data/features/chunks.jsonl`: 청킹 결과

**출력**:

- `data/index/chroma/`: ChromaDB 벡터 인덱스

**체크리스트**:

- [ ] 임베딩 생성 성공
- [ ] ChromaDB 인덱스 생성 확인
- [ ] 인덱싱 리포트 확인

---

### Step 4: 검색 테스트 (Retrieval)

```bash
python entrypoint/inference.py \
    --config config/local.yaml \
    --mode search \
    --query "교육 관련 사업"
```

**참고 문서**: `agent/RETRIEVAL_AGENT.md`

**모드**:

- `search`: 검색만 수행
- `qa`: 질문 답변
- `summarize`: 문서 요약
- `extract`: 정보 추출

---

### Step 5: 질문 답변 (Generation)

```bash
export OPENAI_API_KEY=your_key_here
python entrypoint/inference.py \
    --config config/local.yaml \
    --mode qa \
    --query "이 사업의 평가 기준은 무엇인가요?"
```

**참고 문서**: `agent/GENERATION_AGENT.md`

**추가 옵션**:

```bash
# 문서 요약
python entrypoint/inference.py \
    --config config/local.yaml \
    --mode summarize \
    --doc-id "doc1"

# 정보 추출
python entrypoint/inference.py \
    --config config/local.yaml \
    --mode extract \
    --doc-id "doc1"
```

---

### Step 6: 시스템 평가 (Evaluation)

```bash
# 평가셋 준비 필요: data/eval/test_set.jsonl
python entrypoint/evaluate.py \
    --config config/local.yaml \
    --test-set data/eval/test_set.jsonl
```

**참고 문서**: `agent/EVAL_AGENT.md`

**평가셋 형식** (`data/eval/test_set.jsonl`):

```json
{
  "query": "교육 관련 사업의 예산은?",
  "ground_truth_answer": "1억 3천만원",
  "relevant_doc_ids": ["doc1"],
  "evidence_chunks": ["chunk1"],
  "query_type": "factual"
}
```

**출력**:

- `data/eval/reports/report_*.json`: 평가 리포트

---

## 🔍 문제 해결

### 1. 모듈 Import 오류

```bash
# 프로젝트 루트에서 실행 확인
cd /Users/sinjinseob/Documents/_shin/codeit_ai_middle_project
python entrypoint/train.py --config config/local.yaml
```

### 2. OpenAI API 키 오류

**에러 메시지**: `OPENAI_API_KEY not found in environment`

**해결 방법**:

```bash
# 1. 환경변수 설정
export OPENAI_API_KEY=sk-your-api-key-here

# 2. 확인
echo $OPENAI_API_KEY

# 3. 다시 실행
python entrypoint/train.py --config config/local.yaml --step all
```

**서버에서 영구 설정** (선택):

```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
echo 'export OPENAI_API_KEY=sk-your-api-key-here' >> ~/.bashrc
source ~/.bashrc
```

**자세한 내용**: [ENV_SETUP.md](./ENV_SETUP.md) 참조

### 3. 파일 경로 오류

- 설정 파일에서 경로 확인: `config/local.yaml`
- 상대 경로는 프로젝트 루트 기준

### 4. 의존성 오류

```bash
# 패키지 재설치
pip install --upgrade -r requirements.txt
```

---

## 📊 실행 순서 요약

### 전체 파이프라인 (처음부터)

```bash
# 1. 환경 설정
export OPENAI_API_KEY=your_key_here
pip install -r requirements.txt

# 2. 데이터 준비
# - data/files/에 문서 배치
# - data/data_list.csv 준비

# 3. 전체 파이프라인 실행
python entrypoint/train.py --config config/local.yaml --step all

# 4. 검색 테스트
python entrypoint/inference.py --config config/local.yaml --mode search --query "테스트"

# 5. Q&A 테스트
python entrypoint/inference.py --config config/local.yaml --mode qa --query "질문"
```

### 단계별 실행

```bash
# Step 1: Ingest
python entrypoint/train.py --config config/local.yaml --step ingest

# Step 2: Chunking
python entrypoint/train.py --config config/local.yaml --step chunking

# Step 3: Indexing
python entrypoint/train.py --config config/local.yaml --step indexing
```

---

## 📝 설정 파일 주요 항목

### config/local.yaml 주요 설정

```yaml
# Ingest 설정
ingest:
  input_dir: data/files # 입력 디렉토리
  output_dir: data/preprocessed # 출력 디렉토리
  metadata_csv: data/data_list.csv

# Chunking 설정
chunking:
  chunk_size: 1000 # 청크 크기
  chunk_overlap: 200 # 오버랩 크기

# Indexing 설정
indexing:
  embedding_model: text-embedding-3-large
  batch_size: 100

# Retrieval 설정
retrieval:
  default_top_k: 10
  use_rerank: true

# Generation 설정
generation:
  llm:
    model: gpt-4o-mini
    temperature: 0.2
```

---

## ✅ 검증 체크리스트

각 단계 완료 후 확인:

### Ingest 완료

- [ ] `data/preprocessed/`에 JSON 파일 생성
- [ ] 로그에 파싱 성공 메시지 확인
- [ ] 에러 파일 없음 확인

### Chunking 완료

- [ ] `data/features/chunks.jsonl` 파일 생성
- [ ] 청크 통계 확인
- [ ] 청크 수가 예상 범위 내

### Indexing 완료

- [ ] `data/index/chroma/` 디렉토리 생성
- [ ] 인덱싱 리포트 확인
- [ ] 임베딩 생성 성공 확인

### Retrieval 테스트

- [ ] 검색 결과 반환 확인
- [ ] 응답 시간 2초 이내
- [ ] 결과에 메타데이터 포함

### Generation 테스트

- [ ] 답변 생성 성공
- [ ] 출처 문서 명시 확인
- [ ] 답변 품질 확인

---

## 🔗 관련 문서 링크

- **프로젝트 구조**: `README.md`
- **요구사항**: `agent/PRD.md`
- **일정**: `agent/PLAN.md`
- **에이전트 가이드**: `agent/*_AGENT.md`

---

## 💡 팁

1. **처음 실행 시**: `--step all`로 전체 파이프라인 실행
2. **개발 중**: 각 단계별로 실행하여 디버깅 용이
3. **로그 확인**: 로그 레벨을 DEBUG로 설정하여 상세 정보 확인
4. **에러 발생 시**: 해당 에이전트의 프롬프트 문서 참고

---

**마지막 업데이트**: 2024
