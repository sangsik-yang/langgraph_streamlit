import streamlit as st
import uuid
import pandas as pd
import asyncio
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from chatbot import get_graph_app
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
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
    conn.close()

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

def get_db_tables():
    """Returns a list of table names and their row counts from data.db"""
    if not os.path.exists("data.db"):
        return []
    try:
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        table_info = []
        for table in tables:
            name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {name}")
            count = cursor.fetchone()[0]
            table_info.append((name, count))
        
        conn.close()
        return table_info
    except Exception as e:
        return []

def delete_all_sessions():
    # 1. Clear session metadata
    conn = sqlite3.connect("sessions_meta.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_sessions")
    conn.commit()
    conn.close()
    
    # 2. Clear LangGraph checkpoints (delete the file and let it be recreated)
    if os.path.exists("checkpoints.db"):
        try:
            os.remove("checkpoints.db")
        except Exception as e:
            # If file is locked, we can at least clear the tables
            conn = sqlite3.connect("checkpoints.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM checkpoints")
            cursor.execute("DELETE FROM writes")
            conn.commit()
            conn.close()

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
if "web_search_result" not in st.session_state:
    st.session_state.web_search_result = None
if "image_path" not in st.session_state:
    st.session_state.image_path = None
if "generated_code" not in st.session_state:
    st.session_state.generated_code = None

async def get_session_history(thread_id):
    async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
        app_graph = get_graph_app(checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        state = await app_graph.aget_state(config)
        return state.values

# 3. Sidebar
with st.sidebar:
    st.title("Settings")
    model_option = st.selectbox(
        "Select Model",
        ("gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp", "gemini-2.5-flash-lite"),
        index=3
    )

    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.sql_data = None
        st.session_state.generated_sql = None
        st.session_state.web_search_result = None
        st.session_state.image_path = None
        st.session_state.generated_code = None
        st.rerun()
    
    st.divider()
    st.subheader("🗄️ Database Tables")
    tables = get_db_tables()
    if tables:
        for name, count in tables:
            st.text(f"• {name} ({count} rows)")
    else:
        st.info("No tables found in data.db")

    st.divider()
    st.subheader("📜 Chat History")
    
    if st.button("🗑️ Clear All History", help="Delete all chat sessions and checkpoints"):
        delete_all_sessions()
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.sql_data = None
        st.session_state.generated_sql = None
        st.session_state.web_search_result = None
        st.session_state.image_path = None
        st.session_state.generated_code = None
        st.success("All history cleared!")
        st.rerun()

    sessions = get_all_sessions()
    for tid, title in sessions:
        if st.button(f"💬 {title[:25]}...", key=tid):
            st.session_state.thread_id = tid
            # Fetch messages from graph state
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                values = loop.run_until_complete(get_session_history(tid))
                loop.close()
                st.session_state.messages = values.get("messages", [])
                st.session_state.sql_data = values.get("sql_data")
                st.session_state.generated_sql = values.get("generated_sql")
                st.session_state.web_search_result = values.get("web_search_result")
                st.session_state.image_path = values.get("image_path")
                st.session_state.generated_code = values.get("generated_code")
            except Exception as e:
                st.error(f"Error loading history: {e}")
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

# Define async function for streaming
async def run_agent(prompt, response_placeholder):
    async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
        app_graph = get_graph_app(checkpointer)
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        inputs = {
            "messages": [HumanMessage(content=prompt)],
            "current_model": model_option
        }
        
        full_response = ""
        async for event in app_graph.astream(inputs, config=config, stream_mode="messages"):
            msg, metadata = event
            if msg.content and not isinstance(msg, HumanMessage):
                if metadata.get("langgraph_node") == "oracle":
                    full_response += msg.content
                    response_placeholder.markdown(full_response + "▌")
            
        final_state = await app_graph.aget_state(config)
        st.session_state.sql_data = final_state.values.get("sql_data")
        st.session_state.generated_sql = final_state.values.get("generated_sql")
        st.session_state.image_path = final_state.values.get("image_path")
        st.session_state.generated_code = final_state.values.get("generated_code")
        st.session_state.web_search_result = final_state.values.get("web_search_result")
        
        return full_response

# Handle Input
if prompt := st.chat_input("What would you like to know about sales or products?"):
    if not any(isinstance(m, HumanMessage) for m in st.session_state.messages):
        save_session(st.session_state.thread_id, prompt)

    user_msg = HumanMessage(content=prompt)
    st.session_state.messages.append(user_msg)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            full_response = loop.run_until_complete(run_agent(prompt, response_placeholder))
            loop.close()
        except Exception as e:
            st.error(f"Error running agent: {e}")
            full_response = "에러가 발생했습니다."
        
        response_placeholder.markdown(full_response)
        st.session_state.messages.append(AIMessage(content=full_response))

# 5. Result Explorer (Unified Tabs)
st.divider()
st.subheader("🔍 Result Explorer")
t1, t2, t3, t4, t5 = st.tabs(["📊 Data Table", "📜 SQL Query", "🌐 Web Search Results", "📈 Visualization", "💻 Python Code"])

with t1:
    if st.session_state.sql_data:
        df = pd.DataFrame(st.session_state.sql_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No data table available.")

with t2:
    if st.session_state.generated_sql:
        st.code(st.session_state.generated_sql, language="sql")
    else:
        st.info("No SQL query has been executed.")

with t3:
    if st.session_state.web_search_result:
        st.markdown(st.session_state.web_search_result)
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
