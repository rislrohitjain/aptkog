from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import logging
import polars as pl

from backend.app.services.polars_service import load_excel_sheet, apply_filter_engine, build_hierarchical_tree, clear_cache
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

class RemarkUpdateItem(BaseModel):
    row_index: int
    column: str
    value: Any

class RemarksUpdateRequest(BaseModel):
    filepath: str
    sheet_name: str
    updates: List[RemarkUpdateItem]

@router.post("/update_remarks")
async def update_remarks(payload: RemarksUpdateRequest):
    """
    Saves user-modified Remarks back into the Excel/CSV file on the server.
    """
    if not os.path.exists(payload.filepath):
        raise HTTPException(
            status_code=404,
            detail=f"File not found at path '{payload.filepath}'."
        )

    filename = os.path.basename(payload.filepath).lower()
    try:
        if filename.endswith(".csv"):
            import pandas as pd
            # Load the CSV file
            df_pd = pd.read_csv(payload.filepath)
            
            # Apply all updates
            for item in payload.updates:
                if 0 <= item.row_index < len(df_pd):
                    # Ensure column exists
                    if item.column not in df_pd.columns:
                        if item.column == "Remarks":
                            df_pd.insert(0, "Remarks", "")
                        else:
                            df_pd[item.column] = ""
                    
                    val = item.value
                    if val is None:
                        val = ""
                    df_pd.at[item.row_index, item.column] = val
                    
            # Save back to disk
            df_pd.to_csv(payload.filepath, index=False)
            
        else:
            # Excel (.xlsx)
            import openpyxl
            wb = openpyxl.load_workbook(payload.filepath)
            if payload.sheet_name not in wb.sheetnames:
                raise HTTPException(
                    status_code=404,
                    detail=f"Sheet '{payload.sheet_name}' not found in Excel workbook."
                )
            
            ws = wb[payload.sheet_name]
            
            # Map existing headers to column indices
            col_map = {}
            for col_idx in range(1, ws.max_column + 1):
                header_val = ws.cell(row=1, column=col_idx).value
                if header_val is not None:
                    col_map[str(header_val)] = col_idx
                    
            # Apply updates
            for item in payload.updates:
                col_name = item.column
                if not col_name:
                    continue
                
                # If column not in col_map, we must add it
                if col_name not in col_map:
                    if col_name == "Remarks":
                        # Insert Remarks at first column
                        ws.insert_cols(1)
                        ws.cell(row=1, column=1, value="Remarks")
                        # Shift existing col indices in col_map
                        col_map = {k: (v + 1) for k, v in col_map.items()}
                        col_map["Remarks"] = 1
                    else:
                        # Append other columns to the end
                        new_col_idx = ws.max_column + 1
                        ws.cell(row=1, column=new_col_idx, value=col_name)
                        col_map[col_name] = new_col_idx
                        
                excel_col = col_map[col_name]
                excel_row = item.row_index + 2
                val = item.value
                if val is None:
                    val = ""
                ws.cell(row=excel_row, column=excel_col, value=str(val))
                
            wb.save(payload.filepath)
            wb.close()
            
        # Evict the file from Polars cache to ensure next read fetches updated file
        clear_cache()
        
        return {"status": "success", "message": f"Successfully updated {len(payload.updates)} cell(s) in {payload.filepath}"}
        
    except Exception as e:
        logger.error(f"Failed to update remarks in file: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while updating the remarks: {str(e)}"
        )
