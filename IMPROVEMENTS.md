# 데이터 전처리 및 청킹 개선 사항

## 개요

EDA 결과를 바탕으로 데이터 전처리와 청킹 로직을 개선했습니다.

## 주요 개선 사항

### 1. 데이터 전처리 개선 (`src/ingest/data_preprocessor.py`)

#### 해결한 문제들:
- **결측치 처리**:
  - 공고 번호 18% → 파일명에서 추출 또는 자동 생성
  - 공고 차수 18% → 기본값 0으로 채움
  - 입찰 참여 시작일 26% → 공개 일자 + 1시간으로 기본값 설정

- **데이터 타입 변환**:
  - 사업 금액: 숫자형으로 변환, 이상치 감지 및 로깅
  - 날짜 필드: 다양한 형식 지원 (YYYY-MM-DD HH:MM:SS, YYYY-MM-DD)

- **데이터 정제**:
  - 발주 기관명 공백 정리
  - 중복 공백 제거

- **데이터 요약 생성**:
  - 파일 타입 분포
  - 메타데이터 완성도
  - 예산 통계
  - 시간 분포 통계

### 2. 최적화된 청킹 (`src/chunking/optimized_chunker.py`)

#### 개선 사항:
- **파일 타입별 최적화** (EDA 기반):
  - PDF: 청크 크기 1200자, overlap 200자 (평균 85K자 문서)
  - HWP: 청크 크기 800자, overlap 150자 (평균 6K자 문서)
  - DOCX: 청크 크기 1000자, overlap 200자

- **Overlap 최적화**:
  - 기존: 91.4% overlap (문제)
  - 개선: 최대 30% overlap으로 제한
  - 문장 경계 인식으로 자연스러운 분할

- **문장 경계 인식**:
  - 문장 끝(., !, ?, 。) 인식
  - 문단 경계(\n\n) 인식
  - 의미 단위 보존

### 3. 향상된 Ingest Agent (`src/ingest/enhanced_ingest_agent.py`)

#### 기능:
- 전처리 → 요약 생성 → 문서 파싱 통합 파이프라인
- 자동으로 전처리된 CSV 저장
- 데이터 요약 JSON 생성

## 사용 방법

### 설정 (`config/local.yaml`)

```yaml
ingest:
  use_enhanced: true  # 향상된 ingest 사용

chunking:
  use_optimized: true  # 최적화된 청킹 사용
```

### 실행

```bash
# 전체 파이프라인 실행
python entrypoint/train.py --config config/local.yaml --step all

# Ingest만 실행
python entrypoint/train.py --config config/local.yaml --step ingest

# 청킹만 실행
python entrypoint/train.py --config config/local.yaml --step chunking
```

### 출력 파일

1. **전처리된 CSV**: `data/data_list_preprocessed.csv`
   - 결측치 처리된 메타데이터

2. **데이터 요약**: `data/data_summary.json`
   - 파일 타입 분포
   - 메타데이터 완성도
   - 예산/시간 통계

3. **전처리된 문서**: `data/preprocessed/*.json`
   - 파싱된 텍스트 + 정제된 메타데이터

4. **청크**: `data/features/chunks.jsonl`
   - 최적화된 청킹 결과

## EDA 기반 개선 효과

### Before (EDA 결과):
- Overlap 비율: 91.4% (너무 높음)
- 결측치: 공고 번호 18%, 입찰 시작일 26%
- 청크 크기: 평균 966자 (목표 1000자에 근접)

### After (예상):
- Overlap 비율: ~20-30% (최적화)
- 결측치: 0% (자동 처리)
- 청크 크기: 파일 타입별 최적화
  - PDF: 1200자
  - HWP: 800자
  - DOCX: 1000자

## 주요 클래스

### `DataPreprocessor`
- `preprocess_metadata_csv()`: CSV 전처리
- `generate_data_summary()`: 데이터 요약 생성

### `OptimizedChunker`
- `chunk()`: 파일 타입별 최적화된 청킹
- 문장 경계 인식
- Overlap 최적화

### `EnhancedIngestAgent`
- `preprocess_and_ingest()`: 통합 파이프라인 실행

## 다음 단계

1. **청킹 품질 평가**: 개선된 청킹 결과의 검색 성능 측정
2. **메타데이터 보강**: 발주 기관명 정규화 강화
3. **섹션 기반 청킹**: 문서 구조 인식 개선
4. **동적 청크 크기**: 문서 길이에 따른 자동 조정

