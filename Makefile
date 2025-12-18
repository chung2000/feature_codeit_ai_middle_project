.PHONY: run-backend run-frontend

# 백엔드 실행 (포트 8002)
run-backend:
	python3 -m uvicorn src.api.app:app --port 8002 --reload

# 프론트엔드 실행 (루트에서 바로 실행)
run-frontend:
	npm run dev --prefix web
