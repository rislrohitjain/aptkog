from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import logging
import polars as pl

from backend.app.services.polars_service import load_excel_sheet, apply_filter_engine, build_hierarchical_tree
from backend.app.services.sklearn_service import run_kmeans_clustering
from backend.app.services.langchain_service import run_semantic_analysis

logger = logging.getLogger(__name__)
router = APIRouter()

class FilterCondition(BaseModel):
    column: str
    operator: str  # '=', '!=', 'Like', 'Contains', 'Starts With', 'Ends With', 'reg_expr', 'Wildcards', '>', '<', '>=', '<=', 'Is Null', 'Is Not Null', 'In', 'Not In'
    value: Any

class FilterRequest(BaseModel):
    filepath: str
    sheet_name: str
    filters: List[FilterCondition] = []
    tree_group_cols: Optional[List[str]] = None
    cluster_cols: Optional[List[str]] = None
    cluster_count: Optional[int] = 3

class ChatRequest(BaseModel):
    filepath: str
    sheet_name: str
    question: str

@router.post("/filter")
async def filter_dataset(payload: FilterRequest):
    """
    Applies the Universal Filter Engine (15+ operators), generates system metrics,
    runs optional Scikit-Learn K-Means clustering, and returns data payloads
    for the Table, Graph, and Hierarchical Tree views.
    """
    if not os.path.exists(payload.filepath):
        raise HTTPException(
            status_code=404, 
            detail=f"Uploaded file not found at path '{payload.filepath}'."
        )

    try:
        # Load raw dataframe
        df_raw = load_excel_sheet(payload.filepath, payload.sheet_name)
        total_records = len(df_raw)
        
        # Apply filters
        filter_dicts = [f.model_dump() for f in payload.filters]
        df_filtered = apply_filter_engine(df_raw, filter_dicts)
        
        # Apply Clustering if requested
        if payload.cluster_cols and len(payload.cluster_cols) > 0:
            cluster_cnt = payload.cluster_count if payload.cluster_count else 3
            df_filtered = run_kmeans_clustering(df_filtered, payload.cluster_cols, cluster_cnt)
            
        filtered_records = len(df_filtered)
        
        # Build views
        # 1. Table View (Limit to 500 records for API performance, but send full schema)
        df_table_sample = df_filtered.head(500)
        table_rows = df_table_sample.to_dicts()
        
        # Columns schema
        schema_dict = {col: str(dtype) for col, dtype in df_filtered.schema.items()}
        
        # 2. Graph View
        # Return a larger sample (e.g. 2000 rows) or full data for Plotly to render on the client
        df_graph_sample = df_filtered.head(2000)
        graph_rows = df_graph_sample.to_dicts()
        
        # 3. Tree View
        # Build hierarchical representation from grouped columns
        # If no grouping columns are specified, default to the first two string/category columns
        group_cols = payload.tree_group_cols
        if not group_cols:
            group_cols = [c for c, dtype in df_filtered.schema.items() if dtype == pl.Utf8][:2]
            
        tree_payload = build_hierarchical_tree(df_filtered, group_cols)
        
        return {
            "metrics": {
                "total_records": total_records,
                "filtered_records": filtered_records,
                "columns_count": len(df_raw.columns)
            },
            "schema": schema_dict,
            "table_data": table_rows,
            "graph_data": graph_rows,
            "tree_data": tree_payload
        }
        
    except Exception as e:
        logger.error(f"Error filtering dataset: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the filter request: {str(e)}"
        )

@router.post("/chat")
async def chat_with_dataset(payload: ChatRequest):
    """
    Submits user queries to LangChain semantic analysis engine.
    """
    if not os.path.exists(payload.filepath):
        raise HTTPException(
            status_code=404, 
            detail=f"Uploaded file not found at path '{payload.filepath}'."
        )
        
    try:
        df = load_excel_sheet(payload.filepath, payload.sheet_name)
        filename = os.path.basename(payload.filepath)
        response = run_semantic_analysis(df, payload.question, filename)
        return {"response": response}
    except Exception as e:
        logger.error(f"Chat analytical helper failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query semantic analyst: {str(e)}"
        )
