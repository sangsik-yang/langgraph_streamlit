# Implementation Plan: Intelligent Data Analysis & Visualization Agent

This document outlines the detailed plan for building a stateful AI agent using LangGraph and Streamlit, featuring Google Gemini LLM, SQL search, web search, and data visualization.

## 1. Tech Stack
*   **LLM:** Google Gemini (via `langchain-google-genai`)
*   **Workflow Framework:** LangGraph
*   **Search Tools:** 
    *   Tavily Search API (Web Search)
    *   SQLite (Structured Data Search)
*   **Data & Visualization:** 
    *   Pandas (Data manipulation & DataFrame rendering)
    *   Matplotlib (Dynamic chart generation)
*   **Frontend:** Streamlit

## 2. LangGraph Architecture & State Design

### A. Agent State (`AgentState`)
The state object will track the following:
*   `messages`: Conversation history (`Annotated[list, add_messages]`).
*   `sql_data`: Storage for the latest SQL query result (as a DataFrame).
*   `image_data`: Storage for generated visualization (Matplotlib figure or base64).
*   `current_model`: The model selected in the UI.

### B. Core Nodes
1.  **`oracle` (LLM Node)**: Uses Google Gemini. Applies a "Sliding Window" strategy to only consider the **last 3 messages** for immediate context, while full history is kept in the checkpointer.
2.  **`web_search`**: Executes web searches via Tavily for real-time information.
3.  **`sql_querier`**: 
    *   Translates natural language to SQL.
    *   Executes queries against the SQLite database.
    *   Updates `sql_data` in the state.
4.  **`visualizer/coder`**: 
    *   Identifies when data is too long for text or requires a chart.
    *   Generates and executes Python code to create Matplotlib visualizations.
5.  **`summarizer`**: Provides concise summaries of SQL results or long search findings.

### C. Persistence & Memory
*   **Checkpointer**: `MemorySaver` will be used to persist state across `thread_id` sessions.
*   **History Trimming**: A pre-processor logic to ensure the LLM node only receives the most relevant (recent 3) messages.

## 3. Streamlit UI & Session Management

### A. Sidebar (Control Panel)
*   **Model Selection**: Dropdown to switch between Gemini models (e.g., 1.5 Pro, 1.5 Flash).
*   **Session Control**: `thread_id` management (generate new/reset).
*   **API Configuration**: Input fields for Google and Tavily API keys.

### B. Main Interface (Canvas)
*   **Chat History**: Standard `st.chat_message` rendering.
*   **Dynamic Data Displays**:
    *   If `sql_data` exists in the current state, render it using `st.dataframe()`.
    *   If `image_data` exists, render the plot using `st.pyplot()`.
*   **Streaming UI**: Use `st.empty()` placeholders to stream LLM tokens in real-time.

## 4. Implementation Milestones

### Phase 1: Environment & Mock Data Setup
*   Setup `requirements.txt` and `.env` template.
*   Initialize a sample SQLite database (e.g., Sales or Employee data).
*   Verify Google Gemini API connectivity.

### Phase 2: Tool Development
*   Implement `SQLQueryTool` with schema awareness.
*   Implement `PythonVisualizerTool` for safe Matplotlib code execution.
*   Implement `WebSearchTool` using Tavily.

### Phase 3: LangGraph Workflow Implementation
*   Define the graph structure with conditional edges.
*   Implement the "Last 3 Messages" trimming logic.
*   Integrate `MemorySaver` for thread-based persistence.

### Phase 4: Streamlit Integration & Optimization
*   Build the main UI components.
*   Implement the sync logic between LangGraph state and Streamlit session state.
*   Handle data-heavy responses by separating text summary from DataFrame/Chart views.
