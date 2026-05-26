from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import os
import io
import logging
from backend.app.services.polars_service import load_excel_sheet, execute_join_vlookup, convert_df_to_excel_bytes

logger = logging.getLogger(__name__)
router = APIRouter()

class JoinRequest(BaseModel):
    filepath_a: str
    sheet_name_a: str
    filepath_b: str
    sheet_name_b: str
    join_key_a: str
    join_key_b: str
    join_type: str  # 'left', 'inner', 'outer'
    select_columns_b: List[str]

@router.post("/join")
async def join_datasets(payload: JoinRequest):
    """
    Executes a vectorized relational join (VLOOKUP / INDEX-MATCH style)
    across two separately uploaded files and returns the consolidated binary Excel.
    """
    if not os.path.exists(payload.filepath_a):
        raise HTTPException(status_code=404, detail=f"File A not found at '{payload.filepath_a}'.")
    if not os.path.exists(payload.filepath_b):
        raise HTTPException(status_code=404, detail=f"File B not found at '{payload.filepath_b}'.")

    try:
        # Load sheets
        df_a = load_excel_sheet(payload.filepath_a, payload.sheet_name_a)
        df_b = load_excel_sheet(payload.filepath_b, payload.sheet_name_b)
        
        # Execute join logic
        joined_df = execute_join_vlookup(
            df_a=df_a,
            df_b=df_b,
            join_key_a=payload.join_key_a,
            join_key_b=payload.join_key_b,
            join_type=payload.join_type,
            select_columns_b=payload.select_columns_b
        )
        
        # Write to excel bytes
        excel_bytes = convert_df_to_excel_bytes(joined_df)
        
        # Save locally in temp directory so it can be viewed and analyzed in tabs
        from backend.app.config import settings
        joined_filename = "joined_output.xlsx"
        joined_filepath = os.path.join(settings.UPLOAD_DIR, joined_filename)
        with open(joined_filepath, "wb") as f:
            f.write(excel_bytes)
            
        # Stream the binary Excel file back
        # Create a file-like object from the bytes
        stream = io.BytesIO(excel_bytes)
        
        headers = {
            "Content-Disposition": "attachment; filename=consolidated_dataset.xlsx",
            "X-Joined-Filepath": os.path.abspath(joined_filepath),
            "Access-Control-Expose-Headers": "X-Joined-Filepath"  # Crucial for CORS
        }
        
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Vectorized join failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Join failed: {str(e)}"
        )
