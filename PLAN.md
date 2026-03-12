# 구현 계획: 지능형 데이터 분석 및 시각화 에이전트

이 문서는 Google Gemini LLM, SQL 검색, 웹 검색 및 데이터 시각화 기능을 갖춘 LangGraph 및 Streamlit 기반의 상태 유지형 AI 에이전트 구축을 위한 상세 계획을 설명합니다.

## 1. 기술 스택
*   **LLM:** Google Gemini (`langchain-google-genai` 사용)
*   **워크플로우 프레임워크:** LangGraph
*   **검색 도구:**
    *   Tavily Search API (웹 검색)
    *   SQLite (구조화된 데이터 검색)
*   **데이터 및 시각화:**
    *   Pandas (데이터 조작 및 DataFrame 렌더링)
    *   Matplotlib (동적 차트 생성)
*   **프론트엔드:** Streamlit

## 2. LangGraph 아키텍처 및 상태 설계

### A. 에이전트 상태 (`AgentState`)
상태 객체는 다음을 추적합니다:
*   `messages`: 대화 히스토리 (`Annotated[list, add_messages]`).
*   `sql_data`: 최신 SQL 쿼리 결과 저장 (DataFrame 형태).
*   `image_data`: 생성된 시각화 저장 (Matplotlib 피규어 또는 base64).
*   `current_model`: UI에서 선택된 모델.
*   `web_search_result`: web search result.

### B. 핵심 노드
1.  **`oracle` (LLM 노드)**: Google Gemini를 사용합니다. 즉각적인 컨텍스트를 위해 **마지막 20개의 메시지**만 고려하는 "Sliding Window" 전략을 적용하며, 전체 히스토리는 체크포인터에 보관됩니다.
2.  **`web_search`**: 실시간 정보를 위해 Tavily를 통해 웹 검색을 실행합니다.
    * web_search 결과를 web_search_result에 업데이트합니다.
3.  **`sql_querier`**:
    *   자연어를 SQL로 변환합니다.
    *   SQLite 데이터베이스에 대해 쿼리를 실행합니다.
    *   상태의 `sql_data`를 업데이트합니다.
4.  **`visualizer/coder`**:
    *   데이터가 텍스트로 보기에 너무 길거나 차트가 필요한 시점을 식별합니다.
    *   Matplotlib 시각화를 생성하기 위한 Python 코드를 생성하고 실행합니다.
5.  **`summarizer`**: SQL 결과나 긴 검색 결과에 대해 간결한 요약을 제공합니다.

### C. 지속성 및 메모리
*   **체크포인터**: `SqliteSaver`를 사용하여 `thread_id` 세션 간의 상태를 유지합니다. (영속적 데이터 보관)
*   **히스토리 다듬기(Trimming)**: LLM 노드가 가장 관련성 높은(최근 20개) 메시지만 수신하도록 하는 전처리 로직입니다.

## 3. Streamlit UI 및 세션 관리

### A. 사이드바 (제어판)
*   **모델 선택**: Gemini 모델 간 전환을 위한 드롭다운 (예: 1.5 Pro, 1.5 Flash, 2.5 Flash Lite).
*   **세션 제어**: `thread_id` 관리 (새로 생성/재설정).
*   **API 설정**: Google 및 Tavily API 키 입력 필드.

### B. 메인 인터페이스 (캔버스)
*   **채팅 히스토리**: 표준 `st.chat_message` 렌더링.
*   **동적 데이터 표시**:
    *   현재 상태에 `sql_data`가 있으면 `st.dataframe()`을 사용하여 렌더링합니다.
    *   `image_data`가 있으면 `st.pyplot()`을 사용하여 플롯을 렌더링합니다.
    *   'web_search_result'가 있으면 st.markdown()을 사용하여 렌더링합니다.
*   **스트리밍 UI**: `st.empty()` 플레이스홀더를 사용하여 LLM 토큰을 실시간으로 스트리밍합니다.

## 4. 구현 마일스톤

### 1단계: 환경 및 모의 데이터 설정
*   `requirements.txt` 및 `.env` 템플릿 설정.
*   샘플 SQLite 데이터베이스 초기화 (예: 판매 또는 직원 데이터).
*   Google Gemini API 연결 확인.

### 2단계: 도구 개발
*   스키마 인지 기능이 포함된 `SQLQueryTool` 구현.
*   안전한 Matplotlib 코드 실행을 위한 `PythonVisualizerTool` 구현.
*   Tavily를 이용한 `WebSearchTool` 구현.

### 3단계: LangGraph 워크플로우 구현
*   조건부 엣지를 포함한 그래프 구조 정의.
*   "마지막 20개 메시지" 다듬기 로직 구현.
*   스레드 기반 지속성을 위하여 sqlite 기반 메모리 관리.

### 4단계: Streamlit 통합 및 최적화
*   메인 UI 컴포넌트 구축.
*   LangGraph 상태와 Streamlit 세션 상태 간의 동기화 로직 구현.
*   텍스트 요약과 DataFrame/차트 뷰를 분리하여 데이터가 많은 응답 처리.
