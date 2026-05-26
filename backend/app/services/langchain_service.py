import os
from typing import Dict, Any, List
import polars as pl
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from backend.app.config import settings

def run_semantic_analysis(df: pl.DataFrame, question: str, filename: str) -> str:
    """
    Executes a semantic data inquiry using LangChain.
    If an OpenAI key is configured, it sends schema + question to OpenAI.
    Otherwise, it returns a local heuristic explanation to maintain 100% offline capacity.
    """
    # Build schema summary
    schema = df.schema
    row_count = len(df)
    cols_summary = []
    for col_name, dtype in schema.items():
        # Get unique count or basic metrics if small
        unique_cnt = df[col_name].n_unique()
        null_cnt = df[col_name].null_count()
        cols_summary.append(f"- {col_name} (Type: {dtype}, Uniques: {unique_cnt}, Nulls: {null_cnt})")
        
    cols_str = "\n".join(cols_summary)
    
    # Prompt Template
    prompt_text = """
    You are Antigravity 2.0 AI Data Assistant. You are analyzing a dataset uploaded by the user.
    
    Dataset Context:
    - File Name: {filename}
    - Total Rows: {row_count}
    - Columns and Schema:
    {columns_schema}
    
    User Question: {question}
    
    Please provide a concise, data-driven analytical response or suggest relevant filters and queries. Keep it professional and focus on the data structure.
    """
    
    # Check if OPENAI_API_KEY is configured
    api_key = os.environ.get("OPENAI_API_KEY", settings.OPENAI_API_KEY)
    
    # Check if it looks like a valid key (not placeholder like "mock-key", "your-openai-api-key-here" or empty)
    is_valid_key = api_key and not any(placeholder in api_key.lower() for placeholder in ["mock", "your", "api", "key", "openai"])
    
    if is_valid_key:
        try:
            # We lazy import to prevent slow startups if keys aren't used
            from langchain_openai import ChatOpenAI
            
            prompt = PromptTemplate.from_template(prompt_text)
            llm = ChatOpenAI(temperature=0, api_key=api_key, model_name="gpt-3.5-turbo")
            chain = prompt | llm | StrOutputParser()
            
            response = chain.invoke({
                "filename": filename,
                "row_count": row_count,
                "columns_schema": cols_str,
                "question": question
            })
            return response
        except Exception as e:
            return f"LangChain execution error: {str(e)}. Fallback to local analysis: This dataset '{filename}' contains {row_count} rows and {len(schema)} columns. Your query '{question}' was processed but API key communication failed."
    else:
        # Local heuristic engine (Mock/Deterministic AI Agent)
        # We can parse the question to give somewhat smart responses!
        q_lower = question.lower()
        if "summary" in q_lower or "describe" in q_lower or "columns" in q_lower:
            return (
                f"### Dataset Schema Summary (Local Engine)\n\n"
                f"The dataset **{filename}** contains **{row_count}** records and **{len(schema)}** columns.\n\n"
                f"**Columns:**\n{cols_str}\n\n"
                f"*Hint: Configure a valid `OPENAI_API_KEY` in the `.env` file to enable full GPT-based semantic dialogue.*"
            )
        elif "missing" in q_lower or "null" in q_lower:
            nulls = [f"{col}: {df[col].null_count()}" for col in df.columns if df[col].null_count() > 0]
            nulls_str = "\n".join([f"- {n}" for n in nulls]) if nulls else "No missing values found!"
            return (
                f"### Missing Data Analysis\n\n"
                f"Columns with nulls in **{filename}**:\n{nulls_str}\n\n"
                f"You can apply the **Is Null** or **Is Not Null** operator in the Filter Engine to handle these records."
            )
        else:
            # General fallback suggestion
            suggested_cols = [c for c, t in schema.items() if t in [pl.Int64, pl.Float64]]
            sug_str = f"numeric columns like {suggested_cols[:2]}" if suggested_cols else "available columns"
            return (
                f"### Local Semantic Analyst Response\n\n"
                f"Regarding your inquiry: \"*{question}*\"\n\n"
                f"I detected that the dataset **{filename}** has **{row_count}** rows. "
                f"To inspect patterns in your data, you can build a Pivot Table using {sug_str} or filter rows using our 15-operator engine.\n\n"
                f"*Note: Running in local privacy mode. Set a valid `OPENAI_API_KEY` in `.env` to unlock advanced LLM analytical answering.*"
            )
