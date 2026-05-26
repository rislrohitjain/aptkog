import os
import re
import io
import polars as pl
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Simple in-memory cache for loaded dataframes to prevent reloading large Excel files on every filter/pivot
# Key: (filepath, sheet_name), Value: pl.DataFrame
_DATAFRAME_CACHE: Dict[Tuple[str, str], pl.DataFrame] = {}

def clear_cache():
    _DATAFRAME_CACHE.clear()

def load_excel_sheet(filepath: str, sheet_name: str) -> pl.DataFrame:
    """
    Loads a sheet from an Excel file or parses a CSV file using Polars.
    """
    cache_key = (filepath, sheet_name)
    if cache_key in _DATAFRAME_CACHE:
        logger.info(f"Loading from cache: {cache_key}")
        return _DATAFRAME_CACHE[cache_key]

    logger.info(f"Loading file: {filepath}, sheet/csv: {sheet_name}")
    filename = os.path.basename(filepath)
    
    if filename.lower().endswith(".csv"):
        try:
            df = pl.read_csv(filepath)
        except Exception as e:
            logger.error(f"Failed to load CSV file: {e}")
            raise e
    else:
        try:
            # calamine engine is much faster and uses less memory for large Excel files
            df = pl.read_excel(filepath, sheet_name=sheet_name, engine="calamine")
        except Exception as e:
            logger.warning(f"Calamine engine failed, falling back to openpyxl: {e}")
            df = pl.read_excel(filepath, sheet_name=sheet_name, engine="openpyxl")
    
    # Cache the dataframe
    # Limit cache size to prevent memory leaks with large datasets
    if len(_DATAFRAME_CACHE) >= 5:
        # Evict oldest entry
        oldest_key = next(iter(_DATAFRAME_CACHE))
        _DATAFRAME_CACHE.pop(oldest_key)
        
    _DATAFRAME_CACHE[cache_key] = df
    return df

def get_excel_metadata(filepath: str) -> dict:
    """
    Extracts sheet names and basic info. Supports Excel and CSV files.
    """
    filename = os.path.basename(filepath)
    if filename.lower().endswith(".csv"):
        sheet_names = ["Default"]
    else:
        try:
            from python_calamine import CalamineWorkbook
            workbook = CalamineWorkbook.from_path(filepath)
            sheet_names = workbook.sheet_names
        except Exception as e:
            logger.warning(f"Calamine workbook loading failed, falling back to openpyxl: {e}")
            import openpyxl
            wb = openpyxl.load_workbook(filepath, read_only=True)
            sheet_names = wb.sheetnames
            wb.close()
    
    metadata = {
        "filename": filename,
        "filepath": filepath,
        "sheet_names": sheet_names,
        "file_size_mb": round(os.path.getsize(filepath) / (1024 * 1024), 2)
    }
    return metadata

def apply_filter_engine(df: pl.DataFrame, filters: List[Dict[str, Any]]) -> pl.DataFrame:
    """
    Applies up to 16 different operators mapped to Polars expressions.
    Each filter has 'column', 'operator', and 'value'.
    """
    if not filters:
        return df

    exprs = []
    for f in filters:
        col_name = f.get("column")
        op = f.get("operator")
        val = f.get("value")
        
        if not col_name or not op:
            continue
            
        col_expr = pl.col(col_name)
        col_dtype = df.schema.get(col_name)
        
        # Cast value based on column datatype to avoid Polars strict type matching errors
        typed_val = val
        if val is not None and col_dtype is not None:
            if col_dtype.is_numeric():
                try:
                    if col_dtype.is_integer():
                        # Parse float first in case string is like "1.0"
                        typed_val = int(float(val))
                    else:
                        typed_val = float(val)
                except (ValueError, TypeError):
                    pass
            elif col_dtype == pl.Boolean:
                val_str = str(val).lower()
                if val_str in ["true", "1", "t", "y", "yes"]:
                    typed_val = True
                elif val_str in ["false", "0", "f", "n", "no"]:
                    typed_val = False
        
        # Mapping 15+ comparison operators to Polars expressions
        if op == "=":
            exprs.append(col_expr == typed_val)
        elif op == "!=":
            exprs.append(col_expr != typed_val)
        elif op == "Like":
            # SQL-like Case-insensitive matching, e.g. %abc%
            val_str = str(val) if val is not None else ""
            # Escape regex characters and replace SQL wildcards with regex equivalents
            regex_val = re.escape(val_str).replace(r"\%", ".*").replace(r"\_", ".")
            exprs.append(col_expr.cast(pl.Utf8).str.to_lowercase().str.contains(f"(?i)^{regex_val}$"))
        elif op == "Contains":
            val_str = str(val) if val is not None else ""
            exprs.append(col_expr.cast(pl.Utf8).str.contains(re.escape(val_str), literal=False))
        elif op == "Starts With":
            val_str = str(val) if val is not None else ""
            exprs.append(col_expr.cast(pl.Utf8).str.starts_with(val_str))
        elif op == "Ends With":
            val_str = str(val) if val is not None else ""
            exprs.append(col_expr.cast(pl.Utf8).str.ends_with(val_str))
        elif op == "reg_expr":
            val_str = str(val) if val is not None else ""
            exprs.append(col_expr.cast(pl.Utf8).str.contains(val_str, literal=False))
        elif op == "Wildcards":
            # Glob/wildcard matching with * and ?
            val_str = str(val) if val is not None else ""
            regex_val = re.escape(val_str).replace(r"\*", ".*").replace(r"\?", ".")
            exprs.append(col_expr.cast(pl.Utf8).str.contains(f"^{regex_val}$", literal=False))
        elif op == ">":
            exprs.append(col_expr > typed_val if typed_val is not None else pl.lit(True))
        elif op == "<":
            exprs.append(col_expr < typed_val if typed_val is not None else pl.lit(True))
        elif op == ">=":
            exprs.append(col_expr >= typed_val if typed_val is not None else pl.lit(True))
        elif op == "<=":
            exprs.append(col_expr <= typed_val if typed_val is not None else pl.lit(True))
        elif op == "Is Null":
            exprs.append(col_expr.is_null())
        elif op == "Is Not Null":
            exprs.append(col_expr.is_not_null())
        elif op in ["In", "Not In"]:
            if isinstance(val, str):
                val_list = [x.strip() for x in val.split(",") if x.strip()]
            elif isinstance(val, list):
                val_list = val
            else:
                val_list = [val]
                
            # Cast list items to match column type
            typed_val_list = []
            for item in val_list:
                if col_dtype is not None and col_dtype.is_numeric():
                    try:
                        if col_dtype.is_integer():
                            typed_val_list.append(int(float(item)))
                        else:
                            typed_val_list.append(float(item))
                    except (ValueError, TypeError):
                        typed_val_list.append(item)
                else:
                    typed_val_list.append(item)
                    
            if op == "In":
                exprs.append(col_expr.is_in(typed_val_list))
            else:
                exprs.append(~col_expr.is_in(typed_val_list))
            
    # Combine all expressions with AND
    if exprs:
        for expr in exprs:
            df = df.filter(expr)
            
    return df

def build_hierarchical_tree(df: pl.DataFrame, group_cols: List[str], max_depth: int = 3, max_nodes: int = 100) -> Dict[str, Any]:
    """
    Builds a JSON hierarchical structure for the Tree view of the data.
    Groups dynamically by up to max_depth columns.
    """
    if df.is_empty() or not group_cols:
        return {"name": "Root", "value": len(df), "children": []}

    # Ensure columns exist in dataframe
    valid_cols = [c for c in group_cols if c in df.columns]
    if not valid_cols:
        return {"name": "Root", "value": len(df), "children": []}
        
    valid_cols = valid_cols[:max_depth]
    
    # Recursive helper to build tree
    def get_children(sub_df: pl.DataFrame, cols: List[str], current_depth: int) -> List[Dict[str, Any]]:
        if not cols or sub_df.is_empty() or current_depth >= max_depth:
            return []
            
        col = cols[0]
        # Group by and count
        grouped = sub_df.group_by(col).count().sort("count", descending=True)
        
        # Limit nodes to avoid browser crashes
        grouped = grouped.head(max_nodes)
        
        children = []
        for row in grouped.iter_rows(named=True):
            val = row[col]
            count = row["count"]
            node_name = str(val) if val is not None else "Null"
            
            # Filter subset for next level
            subset_df = sub_df.filter(pl.col(col) == val)
            next_children = get_children(subset_df, cols[1:], current_depth + 1)
            
            node = {"name": node_name, "value": count}
            if next_children:
                node["children"] = next_children
            children.append(node)
            
        return children

    root_children = get_children(df, valid_cols, 0)
    return {
        "name": "Root",
        "value": len(df),
        "children": root_children
    }

def run_pivot_engine(df: pl.DataFrame, index: List[str], columns: List[str], values: str, agg: str) -> pl.DataFrame:
    """
    Executes user-defined pivot table using Polars pivot.
    agg is one of: Sum, Mean, Count, Max, Min
    """
    if not index or not columns or not values:
        raise ValueError("Pivot requires index columns, column grouping, and value column.")
        
    agg_map = {
        "sum": "sum",
        "mean": "mean",
        "count": "count",
        "max": "max",
        "min": "min"
    }
    agg_func = agg_map.get(agg.lower(), "sum")
    
    # Cast values column to Float64 for math ops to avoid str errors (e.g. `sum` operation not supported for dtype `str`)
    if agg_func in ["sum", "mean", "max", "min"]:
        try:
            # We cast to Float64 with strict=False to silently turn non-numeric values into null
            df = df.with_columns(pl.col(values).cast(pl.Float64, strict=False))
        except Exception as e:
            logger.warning(f"Failed to cast pivot values column '{values}' to Float64: {e}")
    
    # Polars pivot expects a single column for 'on'
    # If multiple grouping columns are specified, we pick the first one or concatenate them
    pivot_on = columns[0]
    
    # Run Polars pivot
    pivoted_df = df.pivot(
        values=values,
        index=index,
        on=pivot_on,
        aggregate_function=agg_func
    )
    return pivoted_df

def execute_join_vlookup(
    df_a: pl.DataFrame, 
    df_b: pl.DataFrame, 
    join_key_a: str, 
    join_key_b: str, 
    join_type: str, 
    select_columns_b: List[str],
    select_columns_a: List[str]
) -> pl.DataFrame:
    """
    Executes a vectorized relational join resembling VLOOKUP/INDEX-MATCH.
    """
    if join_key_a not in df_a.columns:
        raise ValueError(f"Join key '{join_key_a}' not found in File A columns.")
    if join_key_b not in df_b.columns:
        raise ValueError(f"Join key '{join_key_b}' not found in File B columns.")
        
    # Ensure key column is included and valid columns are selected from A
    valid_cols_a = list(set([join_key_a] + select_columns_a))
    cols_to_keep_a = [c for c in df_a.columns if c in valid_cols_a]
    df_a_subset = df_a.select(cols_to_keep_a)

    # Ensure key column is included and valid columns are selected from B
    valid_cols_b = [join_key_b] + [c for c in select_columns_b if c in df_b.columns and c != join_key_b]
    df_b_subset = df_b.select(valid_cols_b)
    
    # Execute join
    # map join type (default left join mimics VLOOKUP)
    how_map = {
        "left": "left",
        "inner": "inner",
        "outer": "full"
    }
    how = how_map.get(join_type.lower(), "left")
    
    joined_df = df_a_subset.join(
        df_b_subset,
        left_on=join_key_a,
        right_on=join_key_b,
        how=how
    )
    
    return joined_df

def convert_df_to_excel_bytes(df: pl.DataFrame) -> bytes:
    """
    Writes the Polars DataFrame to a binary Excel file and returns the bytes.
    """
    out_bio = io.BytesIO()
    # write_excel is built-in for Polars if xlsxwriter is installed
    df.write_excel(out_bio, table_name="ConsolidatedData")
    return out_bio.getvalue()
