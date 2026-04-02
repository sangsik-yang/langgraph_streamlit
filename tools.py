import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
import os
import re
from dotenv import load_dotenv

load_dotenv()

READ_ONLY_SQL_PATTERN = re.compile(r"^\s*(WITH|SELECT)\b", re.IGNORECASE)
FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE|ATTACH|DETACH|PRAGMA|VACUUM)\b",
    re.IGNORECASE,
)


def validate_read_only_sql(query: str):
    stripped = query.strip()
    if not stripped:
        raise ValueError("SQL query is empty.")
    if ";" in stripped.rstrip(";"):
        raise ValueError("Only a single read-only SQL statement is allowed.")
    if not READ_ONLY_SQL_PATTERN.match(stripped):
        raise ValueError("Only SELECT and WITH queries are allowed.")
    if FORBIDDEN_SQL_PATTERN.search(stripped):
        raise ValueError("Only read-only SQL queries are allowed.")


def run_read_only_sql(query: str) -> pd.DataFrame:
    validate_read_only_sql(query)
    with sqlite3.connect("file:data.db?mode=ro", uri=True) as conn:
        return pd.read_sql_query(query, conn)


# 1. SQL Query Tool
@tool
def sql_query_tool(query: str):
    """
    Executes a SQL query against the local SQLite database (data.db) 
    and returns the result as a pandas DataFrame.
    Use this for structured data search about products and sales.
    """
    try:
        df = run_read_only_sql(query)
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
def python_visualizer_tool(code: str, output_path: str):
    """
    Executes Python code to generate a matplotlib visualization.
    The code should use the provided output_path when saving the chart.
    Provide the code as a string and a thread-scoped output path.
    """
    try:
        # Cleanup old plot if exists
        output_dir = os.path.dirname(output_path) or "."
        os.makedirs(output_dir, exist_ok=True)
        if os.path.exists(output_path):
            os.remove(output_path)
            
        # Create a local namespace for execution
        local_vars = {}
        # Ensure matplotlib doesn't try to open a window (headless)
        plt.switch_backend("Agg")
        
        # Strip code and ensure correct newlines
        clean_code = code.strip()
        
        exec(clean_code, {"plt": plt, "pd": pd, "output_path": output_path}, local_vars)
        
        if os.path.exists(output_path):
            return f"Visualization generated successfully as '{output_path}'."
        else:
            return f"Code executed but '{output_path}' was not found. Did you forget plt.savefig(output_path)?"
    except Exception as e:
        return f"Python Error: {str(e)}"

# Helper function to get database schema for LLM
def get_db_schema():
    with sqlite3.connect("data.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        schema_info = "Database Schema:\n"
        for table_name in tables:
            table_name = table_name[0]
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            schema_info += f"- Table '{table_name}': {', '.join([col[1] for col in columns])}\n"

    return schema_info
