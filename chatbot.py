from typing import Annotated, TypedDict, List, Optional, Any
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from tools import sql_query_tool, get_web_search_tool, python_visualizer_tool, get_db_schema
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

# 1. State Definition
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    sql_data: Optional[str] # Markdown string of DF for the LLM
    generated_sql: Optional[str] # Capture the raw SQL query
    web_data: Optional[str] # Capture structured data from web search
    image_path: Optional[str]
    generated_code: Optional[str] # Capture the Python code
    current_model: str

# 2. Setup LLM and Tools
def get_model(model_name: str = "gemini-2.0-flash"):
    llm = ChatGoogleGenerativeAI(model=model_name, streaming=True)
    tools = [sql_query_tool, get_web_search_tool(), python_visualizer_tool]
    return llm.bind_tools(tools)

# 3. Define Nodes
def oracle(state: AgentState):
    """The main LLM node that decides the next action."""
    full_history = state["messages"]
    system_msg = [m for m in full_history if isinstance(m, SystemMessage)]
    # Memory Strategy: Sliding Window (Last 20 messages for ~10 rounds of conversation)
    recent_msgs = full_history[-20:] if len(full_history) > 20 else full_history

    if not system_msg:
        prompt_content = f"""You are a senior data analysis assistant. 
{get_db_schema()}

**IMPORTANT: ALWAYS respond in Korean (모든 답변은 한국어로 하세요).**

When using web search:
- If you find tabular data or statistics, explicitly state that you can visualize it.
- You can pass web data to the python_visualizer_tool by writing a python script that creates a DataFrame from the web results you found.

When using python_visualizer_tool:
- ALWAYS use valid Python syntax. 
- You can use either local SQL data OR web data you just found to create charts.
- For web data, create a dict or list in the code first, then convert to pd.DataFrame().
- Ensure each command is on a new line. 
- ALWAYS end with plt.savefig('temp_plot.png').
"""
        system_msg = [SystemMessage(content=prompt_content)]

    input_messages = system_msg + [m for m in recent_msgs if not isinstance(m, SystemMessage)]

    model = get_model(state.get("current_model", "gemini-2.0-flash"))
    response = model.invoke(input_messages)

    return {"messages": [response]}


def tool_node(state: AgentState):
    """Executes tools requested by the LLM."""
    messages = state["messages"]
    last_message = messages[-1]
    
    tool_outputs = []
    sql_markdown = None
    captured_sql = None
    captured_web = None
    image_found = None
    captured_code = None
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        args = tool_call["args"]
        
        if tool_name == "sql_query_tool":
            captured_sql = args.get("query")
            result = sql_query_tool.invoke(args)
            sql_markdown = result
        elif tool_name == "tavily_search_results_json":
            result = get_web_search_tool().invoke(args)
            captured_web = str(result) # Store web search results as context
        elif tool_name == "python_visualizer_tool":
            captured_code = args.get("code")
            result = python_visualizer_tool.invoke(args)
            if "temp_plot.png" in result:
                image_found = "temp_plot.png"
        else:
            result = f"Error: Tool {tool_name} not found."
            
        from langchain_core.messages import ToolMessage
        tool_outputs.append(ToolMessage(
            content=str(result),
            tool_call_id=tool_call["id"]
        ))
        
    return {
        "messages": tool_outputs,
        "sql_data": sql_markdown,
        "generated_sql": captured_sql,
        "web_data": captured_web,
        "image_path": image_found,
        "generated_code": captured_code
    }

# 4. Conditional Logic
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# 5. Build Graph
def create_graph(conn):
    workflow = StateGraph(AgentState)
    workflow.add_node("oracle", oracle)
    workflow.add_node("tools", tool_node)
    workflow.add_edge(START, "oracle")
    workflow.add_conditional_edges("oracle", should_continue, {"tools": "tools", END: END})
    workflow.add_edge("tools", "oracle")
    
    checkpointer = SqliteSaver(conn)
    return workflow.compile(checkpointer=checkpointer)

# Context manager or global connection for the checkpointer
def get_graph_app():
    conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
    return create_graph(conn)

app_graph = get_graph_app()
