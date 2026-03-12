# GEMINI.md - 프로젝트 명령 및 기술 표준

이 문서는 **지능형 데이터 분석 및 시각화 에이전트**를 위한 핵심 명령과 기술 표준을 정의합니다. 이 지침은 일반적인 워크플로우보다 우선합니다.

## 1. 핵심 프로젝트 명령

*   **모델 선택:** 기본 LLM으로 항상 **Google Gemini**(`langchain-google-genai`를 통해)를 사용합니다. (사용 가능한 모델: `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.0-flash-exp`, `gemini-2.5-flash-lite`)
*   **상태 유지 워크플로우:** 모든 에이전트 로직은 **LangGraph**를 사용하여 구성해야 합니다.
*   **메모리 전략 (Sliding Window):**
    *   LLM(`oracle` 노드)은 즉각적인 컨텍스트로 **마지막 20개의 메시지**만 수신해야 합니다.
    *   전체 히스토리는 `thread_id`를 사용하여 LangGraph의 `SqliteSaver(SQLite 기반 체크포인터)`에 보존되어야 합니다.
*   **UI 데이터 분리:**
    *   SQL 결과는 **Streamlit DataFrame**(`st.dataframe`)으로 렌더링해야 합니다.
    *   시각화는 **Matplotlib 피규어**(`st.pyplot`)로 렌더링해야 합니다.
    *   텍스트 요약 및 채팅은 표준 채팅 컨테이너에 유지되어야 합니다.
*   **검색 통합:** 웹 검색에는 **Tavily**를, 구조화된 데이터 쿼리에는 **SQLite**를 사용합니다.

## 2. 기술 표준 및 컨벤션

### A. LangGraph 구현
*   **상태 정의:** `AgentState`에 `TypedDict`를 사용합니다.
*   **노드:** 노드를 모듈화하고 집중된 상태로 유지합니다 (예: `sql_querier`는 SQL 실행만 처리해야 함).
*   **지속성:** 스레드 기반 세션 유지를 위해 `SqliteSaver(SQLite 기반 체크포인터)`를 사용합니다.
*   **스트리밍:** Streamlit UI에서 실시간 토큰 업데이트를 제공하기 위해 비동기 스트리밍(`astream`)을 구현합니다.

### B. Streamlit 통합
*   **세션 상태:** `st.session_state`를 사용하여 LangGraph의 상태와 동기화하고 `thread_id`를 추적합니다.
*   **비동기 브리지:** 모든 비동기 LangGraph 호출이 Streamlit의 동기 실행 환경에 맞게 올바르게 래핑되었는지 확인합니다.
*   **캐싱:** 재실행 시 불필요한 재빌드를 방지하기 위해 LangGraph 인스턴스에 `@st.cache_resource`를 사용합니다.

### C. 데이터 처리
*   **SQL 안전성:** 잘못된 쿼리를 방지하기 위해 자연어-SQL 변환에 스키마 인지(schema-awareness) 기능을 포함합니다.
*   **시각화:** 데이터가 텍스트로 표현하기에 너무 복잡한 경우, 전용 노드(`visualizer/coder`)에서 Matplotlib 코드 생성을 처리해야 합니다.

## 3. 구현 워크플로우

1.  **조사 및 전략:** 노드를 코딩하기 전에 API 키와 DB 스키마를 확인합니다.
2.  **정밀 수정:** 노드를 수정할 때 `AgentState` 전환이 일관되게 유지되는지 확인합니다.
3.  **검증:** 모든 변경 사항은 Streamlit 앱을 실행하고 특정 로직 경로(예: SQL 쿼리 -> DataFrame 렌더링)를 테스트하여 검증해야 합니다.
