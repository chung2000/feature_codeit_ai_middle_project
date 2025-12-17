# 🧪 테스트 가이드 (Testing Guide)

이 문서는 RFP RAG 시스템의 테스트 방법을 설명합니다.

---

## 📋 목차

1. [통합 테스트](#통합-테스트)
2. [단위 테스트](#단위-테스트)
3. [엔드투엔드 테스트](#엔드투엔드-테스트)
4. [성능 테스트](#성능-테스트)

---

## 🔧 통합 테스트

### 실행 방법

```bash
# 프로젝트 루트에서 실행
cd /path/to/codeit_ai_middle_project
python tests/integration_test.py
```

### 테스트 항목

1. **Configuration Loading**: 설정 파일 로딩 확인
2. **Module Imports**: 모든 모듈 import 가능 여부 확인
3. **Directory Structure**: 필요한 디렉토리 생성 확인
4. **Agent Initialization**: 모든 에이전트 초기화 가능 여부 확인

### 예상 결과

```
============================================================
Integration Test Summary
============================================================
✓ PASS: Configuration Loading
✓ PASS: Module Imports
✓ PASS: Directory Structure
✓ PASS: Agent Initialization

Total: 4/4 tests passed
```

---

## 🔬 단위 테스트

### 각 모듈별 테스트

각 모듈은 독립적으로 테스트할 수 있습니다:

#### Ingest Agent 테스트

```bash
# 단일 파일 파싱 테스트
python -c "
from src.ingest.ingest_agent import IngestAgent
from src.common.config import load_config

config = load_config('config/local.yaml')
agent = IngestAgent(config)
result = agent.process_file('data/files/sample.pdf', 'data/preprocessed')
print(result)
"
```

#### Chunking Agent 테스트

```bash
# 청킹 테스트
python -c "
from src.chunking.chunking_agent import ChunkingAgent
from src.common.config import load_config

config = load_config('config/local.yaml')
agent = ChunkingAgent(config)
# ... 테스트 코드
"
```

---

## 🎯 엔드투엔드 테스트

### 전체 파이프라인 테스트

```bash
# 1. 전체 파이프라인 실행
python entrypoint/train.py --config config/local.yaml --step all

# 2. 검색 테스트
python entrypoint/inference.py --config config/local.yaml --mode search --query "테스트 질문"

# 3. Q&A 테스트
python entrypoint/inference.py --config config/local.yaml --mode qa --query "예산은 얼마인가요?"

# 4. 요약 테스트
python entrypoint/inference.py --config config/local.yaml --mode summarize --doc-id "doc_001"

# 5. 정보 추출 테스트
python entrypoint/inference.py --config config/local.yaml --mode extract --doc-id "doc_001"
```

### 검증 체크리스트

- [ ] Ingest: 문서가 정상적으로 파싱되는가?
- [ ] Chunking: 청크가 적절한 크기로 생성되는가?
- [ ] Indexing: 벡터 인덱스가 정상적으로 생성되는가?
- [ ] Retrieval: 검색 결과가 반환되는가?
- [ ] Generation: 답변이 생성되는가?

---

## ⚡ 성능 테스트

### 응답 시간 측정

```bash
# 검색 성능 테스트
time python entrypoint/inference.py --config config/local.yaml --mode search --query "테스트"

# Q&A 성능 테스트
time python entrypoint/inference.py --config config/local.yaml --mode qa --query "질문"
```

### 처리량 테스트

```bash
# 배치 처리 테스트
python entrypoint/train.py --config config/local.yaml --step all
# 처리 시간과 처리량 확인
```

---

## 🐛 문제 해결

### Import 오류

```bash
# 의존성 재설치
pip install -r requirements.txt
```

### 설정 오류

```bash
# 설정 파일 검증
python -c "from src.common.config import load_config; load_config('config/local.yaml')"
```

### 데이터 경로 오류

- `config/local.yaml`에서 경로 확인
- 상대 경로는 프로젝트 루트 기준

---

## 📊 테스트 커버리지

현재 테스트 커버리지:

- ✅ 통합 테스트: 기본 구조
- ⚠️ 단위 테스트: 각 모듈별 테스트 추가 필요
- ✅ 엔드투엔드 테스트: 전체 파이프라인 검증
- ⚠️ 성능 테스트: 벤치마크 추가 필요

---

## 🔄 CI/CD 통합

### GitHub Actions 예시

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python tests/integration_test.py
```

---

## 📝 테스트 데이터

### 샘플 데이터 준비

```bash
# data/files/에 테스트용 PDF/HWP 파일 배치
# data/data_list.csv에 메타데이터 준비
```

### 평가셋 준비

```bash
# data/eval/test_set.jsonl 생성
# 형식: {"query": "...", "ground_truth_answer": "...", ...}
```

---

## ✅ 체크리스트

- [ ] 통합 테스트 통과
- [ ] 각 에이전트 단독 실행 가능
- [ ] 전체 파이프라인 실행 가능
- [ ] 검색 결과 정확도 확인
- [ ] Q&A 답변 품질 확인
- [ ] 성능 요구사항 충족

---

**참고**: 자세한 실행 방법은 [EXECUTION_GUIDE.md](./EXECUTION_GUIDE.md)를 참조하세요.

