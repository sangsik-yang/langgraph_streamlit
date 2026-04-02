from typing import Annotated, TypedDict, List, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from tools import (
    sql_query_tool,
    get_web_search_tool,
    python_visualizer_tool,
    get_db_schema,
    run_read_only_sql,
)
import os
from dotenv import load_dotenv

load_dotenv()

# 1. State Definition
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    sql_data: Optional[List[dict]]
    generated_sql: Optional[str]
    web_search_result: Optional[str]
    image_path: Optional[str]
    generated_code: Optional[str]
    current_model: str
    thread_id: Optional[str]

# 2. Setup LLM and Tools
def get_model(model_name: str = "gemini-2.5-flash-lite"):
    valid_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp", "gemini-2.5-flash-lite"]
    if model_name not in valid_models:
        model_name = "gemini-2.5-flash-lite"
    
    llm = ChatGoogleGenerativeAI(model=model_name, streaming=True)
    tools = [sql_query_tool, get_web_search_tool(), python_visualizer_tool]
    return llm.bind_tools(tools)

# 3. Define Nodes
def oracle(state: AgentState):
    """The main LLM node that decides the next action."""
    full_history = state["messages"]
    
    # 1. Extract System Message
    system_msg = [m for m in full_history if isinstance(m, SystemMessage)]
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
- ALWAYS end with plt.savefig(output_path).
- The variable output_path is already available in the execution environment.
"""
        system_msg = [SystemMessage(content=prompt_content)]

    # 2. Sliding Window Strategy (Last 20 messages as per GEMINI.md mandate)
    # Gemini requires strict sequence: [System] -> [Human] -> [AI(tool)] -> [Tool] -> [AI]
    # To prevent 400 errors, we must ensure ToolMessages are not orphaned from their AI(tool_calls).
    
    raw_recent = full_history[-20:] if len(full_history) > 20 else full_history
    
    # Clean up orphaned messages to satisfy Gemini API constraints
    cleaned_recent = []
    for i, msg in enumerate(raw_recent):
        # Skip ToolMessages if they are the first in the window (they must follow an AI message)
        if isinstance(msg, ToolMessage) and not cleaned_recent:
            continue
        cleaned_recent.append(msg)

    # Final check: Ensure the first message after System is not an AIMessage or ToolMessage
    while cleaned_recent and isinstance(cleaned_recent[0], (ToolMessage, AIMessage)) and not (isinstance(cleaned_recent[0], AIMessage) and cleaned_recent[0].tool_calls):
        cleaned_recent.pop(0)

    input_messages = system_msg + cleaned_recent

    model = get_model(state.get("current_model", "gemini-2.5-flash-lite"))
    response = model.invoke(input_messages)

    return {"messages": [response]}


def tool_node(state: AgentState):
    """Executes tools requested by the LLM."""
    messages = state["messages"]
    last_message = messages[-1]
    
    tool_outputs = []
    structured_sql_data = None
    captured_sql = None
    captured_web = None
    image_found = state.get("image_path")
    captured_code = None
    thread_id = state.get("thread_id") or "default"
    image_output_path = os.path.join("artifacts", f"{thread_id}.png")
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        args = tool_call["args"]
        
        if tool_name == "sql_query_tool":
            captured_sql = args.get("query")
            result = sql_query_tool.invoke(args)
            try:
                if captured_sql:
                    df = run_read_only_sql(captured_sql)
                    structured_sql_data = df.to_dict(orient="records")
            except Exception as e:
                print(f"SQL Data Extraction Error: {e}")
                
        elif tool_name in ["tavily_search_results_json", "tavily_search_results"]:
            search_tool = get_web_search_tool()
            result = search_tool.invoke(args)
            
            # Tavily 결과를 읽기 쉬운 마크다운 형식으로 변환
            if isinstance(result, list):
                markdown_results = "### 🌐 Web Search Findings\n\n"
                for item in result:
                    title = item.get('title', 'No Title')
                    url = item.get('url', '#')
                    content = item.get('content', '')
                    markdown_results += f"**[{title}]({url})**\n\n{content}\n\n---\n"
                captured_web = markdown_results
            else:
                captured_web = str(result)
        elif tool_name == "python_visualizer_tool":
            captured_code = args.get("code")
            tool_args = {
                "code": captured_code,
                "output_path": image_output_path,
            }
            result = python_visualizer_tool.invoke(tool_args)
            if os.path.exists(image_output_path):
                image_found = image_output_path
        else:
            result = f"Error: Tool {tool_name} not found."
            
        tool_outputs.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
        
    return {
        "messages": tool_outputs,
        "sql_data": structured_sql_data,
        "generated_sql": captured_sql,
        "web_search_result": captured_web,
        "image_path": image_found,
        "generated_code": captured_code
    }

def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# 5. Build Graph
def create_graph(checkpointer=None):
    workflow = StateGraph(AgentState)
    workflow.add_node("oracle", oracle)
    workflow.add_node("tools", tool_node)
    workflow.add_edge(START, "oracle")
    workflow.add_conditional_edges("oracle", should_continue, {"tools": "tools", END: END})
    workflow.add_edge("tools", "oracle")
    return workflow.compile(checkpointer=checkpointer)

def get_graph_app(checkpointer=None):
    return create_graph(checkpointer)
