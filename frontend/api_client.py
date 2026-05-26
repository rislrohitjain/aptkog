import os
import requests
from typing import List, Dict, Any, Optional, Tuple

from dotenv import load_dotenv

# Load environment variables from backend/.env if it exists
backend_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", ".env")
load_dotenv(backend_env)

BACKEND_URL = os.environ.get("BACKEND_URL")
if not BACKEND_URL:
    if "SPACE_ID" in os.environ:
        # In Hugging Face Spaces, the backend runs internally on 127.0.0.1:8000
        BACKEND_URL = "http://127.0.0.1:8000"
    else:
        backend_host = os.environ.get("HOST", "127.0.0.1")
        backend_port = os.environ.get("PORT", "8000")
        BACKEND_URL = f"http://{backend_host}:{backend_port}"

class AntigravityAPIClient:
    """
    HTTP Client that routes queries from Streamlit UI to the stateless FastAPI backend.
    """
    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url.rstrip("/")

    def upload_files(self, file_tuples: List[Tuple[str, bytes]]) -> Dict[str, Any]:
        """
        Uploads up to 10 Excel files to the backend.
        file_tuples: list of (filename, file_bytes)
        """
        url = f"{self.base_url}/api/upload"
        files = []
        for name, data in file_tuples:
            if name.lower().endswith(".csv"):
                mime = "text/csv"
            else:
                mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            files.append(("files", (name, data, mime)))
            
        try:
            response = requests.post(url, files=files, timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Upload failed: {str(e)}"}

    def filter_dataset(
        self,
        filepath: str,
        sheet_name: str,
        filters: List[Dict[str, Any]],
        tree_group_cols: Optional[List[str]] = None,
        cluster_cols: Optional[List[str]] = None,
        cluster_count: int = 3
    ) -> Dict[str, Any]:
        """
        Requests universal filtering, clustering, and tri-view representations.
        """
        url = f"{self.base_url}/api/filter"
        payload = {
            "filepath": filepath,
            "sheet_name": sheet_name,
            "filters": filters,
            "tree_group_cols": tree_group_cols or [],
            "cluster_cols": cluster_cols or [],
            "cluster_count": cluster_count
        }
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            err_msg = response.json().get("detail", str(e)) if 'response' in locals() and response else str(e)
            return {"error": f"Filtering failed: {err_msg}"}

    def execute_pivot(
        self,
        filepath: str,
        sheet_name: str,
        index: List[str],
        columns: List[str],
        values: str,
        agg: str
    ) -> Dict[str, Any]:
        """
        Requests custom pivot aggregation.
        """
        url = f"{self.base_url}/api/pivot"
        payload = {
            "filepath": filepath,
            "sheet_name": sheet_name,
            "index": index,
            "columns": columns,
            "values": values,
            "agg": agg
        }
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            err_msg = response.json().get("detail", str(e)) if 'response' in locals() and response else str(e)
            return {"error": f"Pivot failed: {err_msg}"}

    def execute_join(
        self,
        filepath_a: str,
        sheet_name_a: str,
        filepath_b: str,
        sheet_name_b: str,
        join_key_a: str,
        join_key_b: str,
        join_type: str,
        select_columns_a: List[str],
        select_columns_b: List[str]
    ) -> Any:
        """
        Triggers vectorized relational join and returns binary Excel stream.
        """
        url = f"{self.base_url}/api/join"
        payload = {
            "filepath_a": filepath_a,
            "sheet_name_a": sheet_name_a,
            "filepath_b": filepath_b,
            "sheet_name_b": sheet_name_b,
            "join_key_a": join_key_a,
            "join_key_b": join_key_b,
            "join_type": join_type.lower(),
            "select_columns_a": select_columns_a,
            "select_columns_b": select_columns_b
        }
        try:
            response = requests.post(url, json=payload, stream=True, timeout=120)
            response.raise_for_status()
            joined_filepath = response.headers.get("X-Joined-Filepath", "")
            return {
                "content": response.content,
                "joined_filepath": joined_filepath
            }
        except requests.exceptions.RequestException as e:
            err_msg = response.text if 'response' in locals() and response else str(e)
            return {"error": f"Join failed: {err_msg}"}

    def get_diagnostics(self) -> Dict[str, Any]:
        """
        Fetches backend hardware and optimization state.
        """
        url = f"{self.base_url}/api/diagnostics"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Diagnostics retrieval failed: {str(e)}"}

    def ask_analyst(self, filepath: str, sheet_name: str, question: str) -> Dict[str, Any]:
        """
        Asks LangChain AI Data Analyst a semantic question.
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "filepath": filepath,
            "sheet_name": sheet_name,
            "question": question
        }
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            err_msg = response.json().get("detail", str(e)) if 'response' in locals() and response else str(e)
            return {"error": f"LangChain semantic lookup failed: {err_msg}"}
