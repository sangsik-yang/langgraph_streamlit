import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
import os
from dotenv import load_dotenv

load_dotenv()

# 1. SQL Query Tool
@tool
def sql_query_tool(query: str):
    """
    Executes a SQL query against the local SQLite database (data.db) 
    and returns the result as a pandas DataFrame.
    Use this for structured data search about products and sales.
    """
    try:
        conn = sqlite3.connect('data.db')
        df = pd.read_sql_query(query, conn)
        conn.close()
        # Return as string for LLM, but we'll also store the DF in state later
        return df.to_markdown()
    except Exception as e:
        return f"Error executing SQL: {str(e)}"

# 2. Web Search Tool (Tavily)
def get_web_search_tool():
    """Returns the Tavily search tool instance."""
    return TavilySearchResults(max_results=3)

# 3. Python Visualizer Tool
@tool
def python_visualizer_tool(code: str):
    """
    Executes Python code to generate a matplotlib visualization.
    The code should use 'plt.savefig("temp_plot.png")' to save the result.
    Provide the code as a string.
    """
    try:
        # Cleanup old plot if exists
        if os.path.exists("temp_plot.png"):
            os.remove("temp_plot.png")
            
        # Create a local namespace for execution
        local_vars = {}
        # Ensure matplotlib doesn't try to open a window (headless)
        plt.switch_backend('Agg')
        
        # Strip code and ensure correct newlines
        clean_code = code.strip()
        
        exec(clean_code, {"plt": plt, "pd": pd}, local_vars)
        
        if os.path.exists("temp_plot.png"):
            return "Visualization generated successfully as 'temp_plot.png'."
        else:
            return "Code executed but 'temp_plot.png' was not found. Did you forget plt.savefig('temp_plot.png')?"
    except Exception as e:
        return f"Python Error: {str(e)}"

# Helper function to get database schema for LLM
def get_db_schema():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    schema_info = "Database Schema:\n"
    for table_name in tables:
        table_name = table_name[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        schema_info += f"- Table '{table_name}': {', '.join([col[1] for col in columns])}\n"
    
    conn.close()
    return schema_info
