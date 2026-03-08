import streamlit as st
import uuid
import pandas as pd
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from chatbot import app_graph
import os
import sqlite3
from PIL import Image
from dotenv import load_dotenv

# Load environment variables at the start
load_dotenv()

# --- Database for Chat Sessions Metadata ---
def init_session_db():
    conn = sqlite3.connect("sessions_meta.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            thread_id TEXT PRIMARY KEY,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def save_session(thread_id, title):
    conn = sqlite3.connect("sessions_meta.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO chat_sessions (thread_id, title) VALUES (?, ?)", (thread_id, title))
    conn.commit()
    conn.close()

def get_all_sessions():
    conn = sqlite3.connect("sessions_meta.db")
    cursor = conn.cursor()
    cursor.execute("SELECT thread_id, title FROM chat_sessions ORDER BY created_at DESC")
    sessions = cursor.fetchall()
    conn.close()
    return sessions

init_session_db()

# 1. Page Configuration
st.set_page_config(page_title="Intelligent AI Agent", layout="wide")

# 2. Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "sql_data" not in st.session_state:
    st.session_state.sql_data = None
if "generated_sql" not in st.session_state:
    st.session_state.generated_sql = None
if "image_path" not in st.session_state:
    st.session_state.image_path = None
if "generated_code" not in st.session_state:
    st.session_state.generated_code = None

# 3. Sidebar
with st.sidebar:
    st.title("Settings")
    model_option = st.selectbox(
        "Select Model",
        ("gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"),
        index=0
    )

    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.sql_data = None
        st.session_state.generated_sql = None
        st.session_state.web_data = None
        st.session_state.image_path = None
        st.session_state.generated_code = None
        st.rerun()
    
    st.divider()
    st.subheader("📜 Chat History")
    sessions = get_all_sessions()
    for tid, title in sessions:
        if st.button(f"💬 {title[:25]}...", key=tid):
            st.session_state.thread_id = tid
            # Fetch messages from graph state
            config = {"configurable": {"thread_id": tid}}
            state = app_graph.get_state(config)
            st.session_state.messages = state.values.get("messages", [])
            st.session_state.sql_data = state.values.get("sql_data")
            st.session_state.generated_sql = state.values.get("generated_sql")
            st.session_state.image_path = state.values.get("image_path")
            st.session_state.generated_code = state.values.get("generated_code")
            st.rerun()

    st.divider()
    st.write(f"**Current Thread:** `{st.session_state.thread_id}`")
    
    # API Key check
    if not os.getenv("GOOGLE_API_KEY"):
        st.warning("Please set GOOGLE_API_KEY in .env file.")

# 4. Main UI
st.title("🤖 Data Analysis & Visualization Agent")

# Display Chat History
for message in st.session_state.messages:
    if isinstance(message, (HumanMessage, AIMessage)):
        role = "user" if isinstance(message, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(message.content)

# Handle Input
if prompt := st.chat_input("What would you like to know about sales or products?"):
    # If it's a new session, save it with a title
    if not any(isinstance(m, HumanMessage) for m in st.session_state.messages):
        save_session(st.session_state.thread_id, prompt)

    # Append User Message
    user_msg = HumanMessage(content=prompt)
    st.session_state.messages.append(user_msg)
    with st.chat_message("user"):
        st.markdown(prompt)

    # Invoke Graph
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        inputs = {
            "messages": st.session_state.messages,
            "current_model": model_option
        }
        
        # Stream updates
        for event in app_graph.stream(inputs, config=config):
            for node_name, output in event.items():
                if "messages" in output:
                    new_msg = output["messages"][-1]
                    if isinstance(new_msg, AIMessage):
                        full_response += new_msg.content
                        response_placeholder.markdown(full_response + "▌")
                
                # Update session state with graph outputs
                if "sql_data" in output and output["sql_data"]:
                    st.session_state.sql_data = output["sql_data"]
                if "generated_sql" in output and output["generated_sql"]:
                    st.session_state.generated_sql = output["generated_sql"]
                if "image_path" in output and output["image_path"]:
                    st.session_state.image_path = output["image_path"]
                if "generated_code" in output and output["generated_code"]:
                    st.session_state.generated_code = output["generated_code"]

        response_placeholder.markdown(full_response)
        st.session_state.messages.append(AIMessage(content=full_response))

# 5. Result Explorer (Unified Tabs)
st.divider()
st.subheader("🔍 Result Explorer")
t1, t2, t3, t4, t5 = st.tabs(["📊 Data Table", "query_SQL Raw Query", "🌐 Web Search Results", "📈 Visualization", "💻 Python Code"])

with t1:
    if st.session_state.sql_data:
        st.markdown(st.session_state.sql_data)
    else:
        st.info("No data table available.")

with t2:
    if st.session_state.generated_sql:
        st.code(st.session_state.generated_sql, language="sql")
    else:
        st.info("No SQL query has been executed.")

with t3:
    if "web_data" in st.session_state and st.session_state.web_data:
        st.write(st.session_state.web_data)
    else:
        st.info("No web search data available.")

with t4:
    if st.session_state.image_path and os.path.exists(st.session_state.image_path):
        image = Image.open(st.session_state.image_path)
        st.image(image, caption="Generated Visualization", use_container_width=True)
    else:
        st.info("No visualization generated yet.")

with t5:
    if st.session_state.generated_code:
        st.code(st.session_state.generated_code, language="python")
    else:
        st.info("No Python code available.")
