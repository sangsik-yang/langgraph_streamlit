# 🤖 Intelligent Data Analysis & Visualization Agent

LangGraph와 Streamlit을 결합한 지능형 데이터 분석 및 시각화 에이전트입니다. Google Gemini LLM을 사용하여 자연어로 SQL 쿼리, 웹 검색, 그리고 데이터 시각화를 수행할 수 있습니다.

## 🚀 주요 기능

- **Stateful AI Workflow**: LangGraph를 활용한 상태 기반 에이전트 설계.
- **다중 도구 통합 (Multi-Tooling)**:
    - **SQL Search**: 자연어를 SQL로 변환하여 SQLite 데이터베이스 조회.
    - **Web Search**: Tavily API를 통한 실시간 웹 정보 검색 및 요약.
    - **Python Visualizer**: 데이터 분석 결과를 Matplotlib 차트로 자동 시각화.
- **스마트 메모리 관리**:
    - **Sliding Window**: 최근 10회(20개 메시지)의 대화 맥락을 기억하여 정확한 답변 제공.
    - **Persistent History**: SQLite 기반 체크포인터를 사용하여 대화 내역 영구 저장 및 복구.
- **직관적인 UI (Streamlit)**:
    - 실시간 토큰 스트리밍 응답.
    - **Result Explorer**: 데이터 테이블, 실행된 SQL 쿼리, 웹 검색 결과, 시각화 차트, 실행된 Python 코드를 탭별로 분리하여 제공.
    - **Session Manager**: 사이드바를 통한 과거 대화 목록 관리 및 새 대화 시작 기능.

## 🛠 Tech Stack

- **LLM**: Google Gemini 2.0 Flash
- **Framework**: LangGraph, LangChain
- **Frontend**: Streamlit
- **Database**: SQLite (Data & Chat Checkpoints)
- **Tools**: Tavily Search, Pandas, Matplotlib

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

## 🔍 사용 예시

- **데이터 조회**: "현재 판매 중인 제품 목록과 가격을 알려줘."
- **데이터 시각화**: "가장 비싼 제품 TOP 3를 막대 그래프로 그려줘."
- **웹 검색 분석**: "최근 AI 트렌드에 대해 검색하고 주요 키워드를 요약해줘."
- **복합 작업**: "웹에서 스마트폰 시장 점유율을 검색해서 시각화 해줘."

## 📂 프로젝트 구조

- `app.py`: Streamlit 메인 UI 및 세션 관리 로직.
- `chatbot.py`: LangGraph 워크플로우 및 에이전트 노드 정의.
- `tools.py`: SQL, Web Search, Python Code 실행 도구 모음.
- `init_db.py`: 테스트용 SQLite 데이터베이스 생성 스크립트.
- `checkpoints.sqlite`: 대화 내역 영구 저장용 DB.
- `sessions_meta.db`: 대화 목록 메타데이터 저장용 DB.
