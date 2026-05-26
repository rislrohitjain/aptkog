from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import logging
from backend.app.services.polars_service import load_excel_sheet, run_pivot_engine

logger = logging.getLogger(__name__)
router = APIRouter()

class PivotRequest(BaseModel):
    filepath: str
    sheet_name: str
    index: List[str]
    columns: List[str]
    values: str
    agg: str  # 'Sum', 'Mean', 'Count', 'Max', 'Min'

@router.post("/pivot")
async def pivot_dataset(payload: PivotRequest):
    """
    Executes a pivot aggregation on Polars dataframes based on user inputs.
    """
    if not os.path.exists(payload.filepath):
        raise HTTPException(
            status_code=404, 
            detail=f"Uploaded file not found at path '{payload.filepath}'."
        )

    if not payload.index or not payload.columns or not payload.values:
        raise HTTPException(
            status_code=400,
            detail="Pivot configuration must include at least one row index, one column grouping, and one value column."
        )

    try:
        # Load dataset
        df = load_excel_sheet(payload.filepath, payload.sheet_name)
        
        # Verify columns exist
        missing_index = [c for c in payload.index if c not in df.columns]
        missing_cols = [c for c in payload.columns if c not in df.columns]
        
        if missing_index:
            raise HTTPException(status_code=400, detail=f"Index column(s) not found in dataset: {missing_index}")
        if missing_cols:
            raise HTTPException(status_code=400, detail=f"Grouping column(s) not found in dataset: {missing_cols}")
        if payload.values not in df.columns:
            raise HTTPException(status_code=400, detail=f"Values column '{payload.values}' not found in dataset.")

        # Run pivot
        pivoted_df = run_pivot_engine(
            df=df,
            index=payload.index,
            columns=payload.columns,
            values=payload.values,
            agg=payload.agg
        )
        
        # Return as JSON records and headers
        headers = pivoted_df.columns
        records = pivoted_df.to_dicts()
        
        return {
            "columns": headers,
            "data": records,
            "shape": pivoted_df.shape
        }
        
    except Exception as e:
        logger.error(f"Pivot engine operation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Pivot failed: {str(e)}"
        )
