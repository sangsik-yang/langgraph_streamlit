# Research: LangGraph + Streamlit for AI Workflow Agents

This document contains a detailed summary of research findings for building an AI Workflow Agent using LangGraph and Streamlit.

## 1. LangGraph Core Concepts

LangGraph is designed for building stateful, multi-actor applications with LLMs by modeling workflows as cyclic graphs.

### A. State Management
*   **The State Object:** A shared data structure (often `TypedDict` or Pydantic `BaseModel`) that serves as the single source of truth for the workflow.
*   **Reducers:** Functions that define how state updates are merged. A common pattern is appending messages to a list rather than overwriting it.
*   **Immutability:** Nodes return partial updates, and LangGraph merges them into a new version of the state, preserving historical snapshots.

### B. Nodes
*   **Definition:** Python functions or Runnables that take the current `State` as input and return a dictionary of state updates.
*   **Isolation:** Nodes are decoupled, making the workflow modular and easy to test.

### C. Edges
*   **Normal Edges:** Direct transitions from one node to another.
*   **Conditional Edges:** Logic that routes the workflow based on the current state (e.g., branching based on LLM output or tool results).
*   **START/END:** Special markers representing the entry and exit points of the graph.

### D. Persistence (Checkpointers)
*   **Mechanism:** Automatic snapshotting of state at every step using database layers (SQLite, Postgres, etc.).
*   **Threads:** Workflows are organized by `thread_id`, enabling multiple independent conversations.
*   **Features:** Enables "Human-in-the-loop" (pausing for approval), "Time Travel" (replaying state), and fault tolerance.

---

## 2. Streamlit for Agent UIs

Streamlit provides a rapid way to build interactive web interfaces for Python applications.

### A. Chat Interface
*   `st.chat_message`: Creates containers for user and assistant messages.
*   `st.chat_input`: A dedicated input field for user prompts.
*   `st.session_state`: Essential for persisting chat history and graph state across reruns.

### B. Session State Management
*   Streamlit reruns the script from top to bottom on every interaction.
*   Must initialize `st.session_state.messages = []` to prevent data loss.
*   The LangGraph `thread_id` should also be stored in `session_state` to maintain the same conversation thread.

---

## 3. Integration Patterns & Challenges

Combining the two requires bridging Streamlit's synchronous execution with LangGraph's often asynchronous or multi-threaded nature.

### A. The "Async Bridge"
Streamlit runs on a Tornado event loop. To call async agents safely:
```python
import asyncio
import streamlit as st

def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
```

### B. Handling Callbacks (`StreamlitCallbackHandler`)
Using the standard `StreamlitCallbackHandler` with LangGraph is tricky because LangGraph may run nodes in separate threads, losing the `ScriptRunContext`.
*   **The Context Wrapper Solution:** Manually capture and inject the Streamlit context into the callback's `on_` methods using `add_script_run_ctx`.
*   **Manual Streaming (Recommended):** Instead of complex callback wrappers, use `graph.stream(..., stream_mode="messages")` or `"updates"` and iterate over events to update `st.empty()` placeholders.

### C. Streaming Strategies
1.  **`stream_mode="values"`:** Emits the full state after each step.
2.  **`stream_mode="updates"`:** Emits only the partial updates from each node.
3.  **`stream_mode="messages"`:** (Newer LangGraph feature) Specifically for streaming LLM tokens/messages.

---

## 4. Implementation Checklist

1.  **Define State:** Use `TypedDict` to track messages, tool outputs, and intermediate flags.
2.  **Build Graph:** Define nodes (LLM call, Tool execution) and conditional edges.
3.  **Setup Persistence:** Use `MemorySaver` for local development or a DB checkpointer for production.
4.  **UI Layout:**
    *   Sidebar for configuration (API keys, settings).
    *   Main chat window with history rendering.
    *   Streaming logic using `st.chat_message("assistant")` and `st.empty()`.
5.  **Error Handling:** Catch API errors and display them gracefully via `st.error()`.
