import polars as pl
from typing import List
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)

def run_kmeans_clustering(df: pl.DataFrame, columns: List[str], n_clusters: int = 3) -> pl.DataFrame:
    """
    Applies K-Means clustering on selected numeric columns and appends 'Cluster_Label' to the DataFrame.
    Fills missing values with the column mean to preserve row shape.
    """
    if df.is_empty():
        return df
        
    # Filter only valid numeric columns
    numeric_cols = [c for c in columns if c in df.columns and df[c].dtype in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]]
    if len(numeric_cols) < 1:
        logger.warning("No numeric columns provided for clustering.")
        return df

    try:
        # Extract numerical data as numpy array
        # First, fill nulls with column mean to avoid scikit-learn fitting errors
        df_clean = df.select(numeric_cols)
        
        filled_series = []
        for col in numeric_cols:
            mean_val = df_clean[col].mean()
            if mean_val is None:
                mean_val = 0.0
            filled_series.append(df_clean[col].fill_null(mean_val))
            
        df_filled = pl.DataFrame(filled_series)
        X = df_filled.to_numpy()
        
        # Standardize the features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Fit K-Means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
        labels = kmeans.fit_predict(X_scaled)
        
        # Convert labels to string clusters like 'Cluster 1', 'Cluster 2' etc.
        cluster_names = [f"Cluster {label}" for label in labels]
        
        # Add labels to original dataframe
        return df.with_columns(pl.Series("Cluster_Label", cluster_names))
    except Exception as e:
        logger.error(f"K-Means clustering failed: {e}")
        # Return dataframe with all "Cluster 0" if it fails
        return df.with_columns(pl.Series("Cluster_Label", ["Cluster 0"] * len(df)))
