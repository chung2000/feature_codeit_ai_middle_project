# 🔑 환경변수 설정 가이드 (Environment Variables Setup)

이 문서는 RFP RAG 시스템 실행에 필요한 환경변수 설정 방법을 설명합니다.

---

## 📋 필수 환경변수

### OPENAI_API_KEY

OpenAI API를 사용하기 위한 API 키입니다.

**설정 방법 1: 환경변수로 직접 설정**

```bash
# Linux/Mac
export OPENAI_API_KEY=sk-your-api-key-here

# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-your-api-key-here"

# Windows (CMD)
set OPENAI_API_KEY=sk-your-api-key-here
```

**설정 방법 2: .env 파일 사용 (권장)**

프로젝트 루트에 `.env` 파일을 생성:

```bash
# .env 파일
OPENAI_API_KEY=sk-your-api-key-here
```

그리고 Python 스크립트 실행 전에:

```bash
# python-dotenv가 설치되어 있다면 자동으로 로드됩니다
# 또는 수동으로:
export $(cat .env | xargs)
```

**설정 확인**

```bash
# 환경변수 확인
echo $OPENAI_API_KEY

# Python에서 확인
python -c "import os; print('API Key:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"
```

---

## 🚀 서버에서 실행 시

### 방법 1: 세션별 설정 (임시)

```bash
# SSH 접속 후
export OPENAI_API_KEY=sk-your-api-key-here

# 확인
echo $OPENAI_API_KEY

# 파이프라인 실행
python entrypoint/train.py --config config/local.yaml --step all
```

### 방법 2: .bashrc 또는 .zshrc에 추가 (영구)

```bash
# ~/.bashrc 또는 ~/.zshrc 파일에 추가
export OPENAI_API_KEY=sk-your-api-key-here

# 적용
source ~/.bashrc  # 또는 source ~/.zshrc
```

### 방법 3: .env 파일 사용

```bash
# 프로젝트 디렉토리로 이동
cd ~/codeit_ai_middle_project

# .env 파일 생성
echo "OPENAI_API_KEY=sk-your-api-key-here" > .env

# .env 파일 로드 (스크립트 실행 전)
export $(cat .env | xargs)

# 또는 python-dotenv 사용 (설치 필요)
pip install python-dotenv
```

---

## 🔒 보안 주의사항

1. **절대 Git에 커밋하지 마세요**
   - `.env` 파일은 `.gitignore`에 추가되어 있습니다
   - API 키를 코드에 하드코딩하지 마세요

2. **환경변수 확인**
   - 실행 전에 항상 환경변수가 설정되었는지 확인하세요

3. **권한 관리**
   - `.env` 파일 권한: `chmod 600 .env`

---

## 🐛 문제 해결

### 에러: "OPENAI_API_KEY not found in environment"

**원인**: 환경변수가 설정되지 않았습니다.

**해결 방법**:

```bash
# 1. 환경변수 설정
export OPENAI_API_KEY=sk-your-api-key-here

# 2. 확인
echo $OPENAI_API_KEY

# 3. 다시 실행
python entrypoint/train.py --config config/local.yaml --step all
```

### 에러: "Invalid API key"

**원인**: API 키가 잘못되었거나 만료되었습니다.

**해결 방법**:
1. OpenAI 대시보드에서 API 키 확인
2. 새로운 API 키 생성
3. 환경변수 업데이트

---

## 📝 체크리스트

실행 전 확인:

- [ ] `OPENAI_API_KEY` 환경변수 설정됨
- [ ] 환경변수 확인 (`echo $OPENAI_API_KEY`)
- [ ] API 키 형식이 올바름 (`sk-`로 시작)
- [ ] `.env` 파일이 있다면 `.gitignore`에 포함됨

---

## 🔗 관련 문서

- [EXECUTION_GUIDE.md](./EXECUTION_GUIDE.md): 전체 실행 가이드
- [README.md](./README.md): 프로젝트 개요

---

**참고**: API 키는 OpenAI 대시보드(https://platform.openai.com/api-keys)에서 생성할 수 있습니다.

