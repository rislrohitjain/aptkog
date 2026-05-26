from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import logging
from typing import List
from backend.app.config import settings
from backend.app.services.polars_service import get_excel_metadata, clear_cache

logger = logging.getLogger(__name__)
router = APIRouter()

from typing import List, Optional

@router.post("/upload")
async def upload_files(files: Optional[List[UploadFile]] = File(default=None)):
    """
    Accepts up to 10 .xlsx files (max 500MB each).
    Saves to the configured secure local temp directory and returns sheet metadata.
    """
    if not files:
        raise HTTPException(
            status_code=400,
            detail="No files received. Please make sure to upload files using the multi-part form key 'files'."
        )
        
    if len(files) > 10:
        raise HTTPException(
            status_code=400, 
            detail="Too many files. A maximum of 10 files can be uploaded concurrently."
        )

    # Clear cached dataframes to avoid stale data
    clear_cache()
    
    uploaded_metadata = []
    
    for file in files:
        if not file.filename:
            continue
            
        file_ext = os.path.splitext(file.filename.lower())[1]
        if file_ext not in [".xlsx", ".csv"]:
            raise HTTPException(
                status_code=400, 
                detail=f"File '{file.filename}' is not an Excel (.xlsx) or CSV (.csv) file."
            )
            
        # Secure filename by stripping path characters
        safe_filename = os.path.basename(file.filename)
        target_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
        
        try:
            # Write file in chunks to prevent memory issues with large files up to 500MB
            bytes_written = 0
            chunk_size = 1024 * 1024  # 1MB
            
            with open(target_path, "wb") as f:
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    bytes_written += len(chunk)
                    
                    if bytes_written > settings.MAX_CONTENT_LENGTH:
                        # Clean up file and abort
                        f.close()
                        try:
                            os.remove(target_path)
                        except OSError:
                            pass
                        raise HTTPException(
                            status_code=413,
                            detail=f"File '{file.filename}' exceeds the maximum allowed size of 500MB."
                        )
                    f.write(chunk)
            
            logger.info(f"Saved file '{safe_filename}' ({bytes_written} bytes) to {target_path}")
            
            # Extract metadata (sheet names, etc.) using Calamine/openpyxl
            meta = get_excel_metadata(target_path)
            uploaded_metadata.append(meta)
            
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error saving file '{file.filename}': {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process file '{file.filename}': {str(e)}"
            )
            
    return {
        "message": f"Successfully uploaded {len(uploaded_metadata)} file(s).",
        "files": uploaded_metadata
    }
