# AI Agent Team

AI 기반 소프트웨어 개발 자동화 시스템

## 프로젝트 구조

```
agent_team/
├── api/                    # FastAPI 서버
│   └── server.py
├── agents/                 # AI 에이전트 (Planner, Coder, Evaluator)
│   ├── base.py
│   ├── planner.py
│   ├── coder.py
│   └── evaluator.py
├── core/                   # 실행 엔진
│   ├── engine.py
│   └── memory.py
├── config/                 # 설정
│   └── settings.py
├── frontend/               # React 프론트엔드
│   ├── public/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── index.tsx
│   ├── package.json
│   └── tsconfig.json
├── tests/                  # 단위 테스트
├── docker-compose.yml
├── Dockerfile.backend
├── requirements.txt
└── main.py
```

## 실행 방법

### Docker Compose 사용 (권장)

```bash
# 전체 시스템 실행 (백엔드 + 프론트엔드)
docker-compose up --build

# 백엔드만 실행
docker-compose up backend

# 프론트엔드만 실행
docker-compose up frontend
```

### 로컬에서 실행

#### 백엔드 (FastAPI)

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python -m uvicorn api.server:app --reload
```

백엔드 API: http://localhost:8000

#### 프론트엔드 (React)

```bash
cd frontend
npm install
npm start
```

프론트엔드: http://localhost:3000

## API 사용법

### 프로젝트 실행

```bash
POST /api/execute
{
  "project_overview": "Python으로 REST API 서버를 만들어줘"
}
```

### 작업 상태 확인

```bash
GET /api/tasks/{task_id}
```

### 작업 목록

```bash
GET /api/tasks
```

## 개발

### 테스트 실행

```bash
pytest
```

## 라이선스

MIT
