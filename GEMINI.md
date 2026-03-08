# GEMINI.md - Project Mandates & Technical Standards

This document defines the foundational mandates and technical standards for the **Intelligent Data Analysis & Visualization Agent**. These instructions take precedence over general workflows.

## 1. Core Project Mandates

*   **Model Selection:** Always use **Google Gemini** (via `langchain-google-genai`) as the primary LLM.
*   **Stateful Workflow:** All agent logic must be orchestrated using **LangGraph**.
*   **Memory Strategy (Sliding Window):** 
    *   The LLM (`oracle` node) must only receive the **last 3 messages** as immediate context.
    *   Full history must be preserved in the LangGraph `MemorySaver` using `thread_id`.
*   **Data Separation in UI:** 
    *   SQL results must be rendered as **Streamlit DataFrames** (`st.dataframe`).
    *   Visualizations must be rendered as **Matplotlib figures** (`st.pyplot`).
    *   Text summaries and chat must remain in the standard chat containers.
*   **Search Integration:** Use **Tavily** for web searches and **SQLite** for structured data queries.

## 2. Technical Standards & Conventions

### A. LangGraph Implementation
*   **State Definition:** Use `TypedDict` for the `AgentState`. 
*   **Nodes:** Keep nodes modular and focused (e.g., `sql_querier` should only handle SQL execution).
*   **Persistence:** Use `MemorySaver` for thread-based session persistence.
*   **Streaming:** Implement asynchronous streaming (`astream`) to provide real-time token updates in the Streamlit UI.

### B. Streamlit Integration
*   **Session State:** Use `st.session_state` to sync with LangGraph's state and track `thread_id`.
*   **Async Bridge:** Ensure all async LangGraph calls are wrapped correctly for Streamlit's synchronous execution environment.
*   **Caching:** Use `@st.cache_resource` for the LangGraph instance to prevent redundant rebuilds during reruns.

### C. Data Handling
*   **SQL Safety:** Ensure natural-language-to-SQL translation includes schema-awareness to prevent invalid queries.
*   **Visualization:** Matplotlib code generation must be handled by a dedicated node (`visualizer/coder`) when data is too complex for text representation.

## 3. Implementation Workflow

1.  **Research & Strategy:** Verify API keys and DB schemas before coding nodes.
2.  **Surgical Edits:** When modifying nodes, ensure the `AgentState` transitions remain consistent.
3.  **Validation:** Every change must be verified by running the Streamlit app and testing the specific logic path (e.g., SQL query -> DataFrame rendering).
