# 🤖 Intelligent Data Analysis & Visualization Agent

LangGraph와 Streamlit을 결합한 지능형 데이터 분석 및 시각화 에이전트입니다. **Google Gemini 2.5 Flash Lite** 모델을 기본으로 사용하여 자연어로 SQL 쿼리, 실시간 웹 검색, 그리고 데이터 시각화를 수행합니다.

## 🚀 주요 기능

- **Stateful AI Workflow**: **LangGraph**를 활용한 정교한 상태 기반 워크플로우 설계.
- **다중 도구 통합 (Multi-Tooling)**:
    - **SQL Search**: 자연어를 SQL로 변환하여 SQLite(`data.db`)를 **읽기 전용(SELECT/WITH only)** 으로 안전하게 조회.
    - **Web Search**: Tavily API를 통한 실시간 웹 정보 검색 및 마크다운 형식 결과 제공.
    - **Python Visualizer**: 데이터 분석 결과를 Matplotlib 차트로 자동 시각화하고, 세션별 아티팩트 파일로 저장.
- **스마트 메모리 관리**:
    - **Sliding Window**: **최근 20개**의 메시지 맥락을 유지하여 Gemini API 최적화 및 토큰 관리.
    - **Persistent History**: **AsyncSqliteSaver**(`checkpoints.db`)를 사용하여 대화 상태를 영구적으로 저장 및 복구.
    - **Session-safe UI State**: 새 대화 시작, 히스토리 삭제, 세션 복구 시 UI 상태를 일관되게 초기화 및 복원.
- **직관적인 UI (Streamlit)**:
    - **Real-time Streaming**: LLM 응답 토큰 단위 실시간 렌더링.
    - **Result Explorer**: 📊 데이터 테이블, 📜 SQL 쿼리, 🌐 웹 검색 결과, 📈 시각화 차트, 💻 실행 코드를 탭별로 분리하여 제공.
    - **Dashboard Sidebar**: 
        - **🗄️ Database Tables**: 현재 DB의 테이블 목록과 데이터 건수 실시간 표시.
        - **📜 Chat History**: 과거 대화 목록 관리 및 특정 세션 복구.
        - **🗑️ Clear History**: 한 번의 클릭으로 모든 대화 내역, 체크포인트, 생성된 시각화 아티팩트 초기화.

## 🛠 Tech Stack

- **LLM**: **Google Gemini 2.5 Flash Lite** (default), 1.5 Pro, 2.0 Flash
- **Framework**: LangGraph, LangChain
- **Frontend**: Streamlit
- **Database**: SQLite (Data, Meta, & Chat Checkpoints)
- **Tools**: Tavily Search, Pandas, Matplotlib, aiosqlite

## ⚙️ 설치 및 실행 방법

### 1. 환경 변수 설정
`.env` 파일을 생성하고 본인의 API 키를 입력합니다.
```text
GOOGLE_API_KEY=your_google_api_key
TAVILY_API_KEY=your_tavily_api_key
```

### 2. 패키지 설치 및 가상 환경 구축
```bash
# 가상 환경 생성
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 샘플 데이터베이스 초기화
```bash
python3 init_db.py
```

### 4. 앱 실행
```bash
streamlit run app.py
```

## 📂 프로젝트 구조

- `app.py`: Streamlit 메인 UI, 비동기 에이전트 브리지, 세션 메타데이터 관리, UI 상태 초기화/복원 로직.
- `chatbot.py`: LangGraph 워크플로우, `oracle` 노드(메시지 정제 로직 포함), 세션별 시각화 경로를 포함한 `tool_node` 정의.
- `tools.py`: 읽기 전용 SQL 검증/실행, Tavily 웹 검색, 세션별 이미지 저장을 지원하는 Python 시각화 도구 및 스키마 제공 기능.
- `init_db.py`: 테스트용 `data.db` 생성 스크립트.
- `checkpoints.db`: LangGraph 대화 상태 영구 저장용 SQLite DB.
- `sessions_meta.db`: 사이드바 대화 목록 메타데이터 저장용 DB.
- `artifacts/`: 세션별 생성 차트 이미지(`{thread_id}.png`) 저장 디렉터리.
