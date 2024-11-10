# utils/data_cleaning.py

import pandas as pd
import logging

# Initialize logging
logger = logging.getLogger(__name__)

def clean(df):
    """
    Cleans the DataFrame by dropping any rows with missing values.
    
    Parameters:
    - df (pd.DataFrame): The input DataFrame to be cleaned.
    
    Returns:
    - pd.DataFrame: The cleaned DataFrame with no missing values.
    """
    try:
        initial_shape = df.shape
        # Drop rows with any missing values
        df_cleaned = df.dropna(axis=0, how='any')
        final_shape = df_cleaned.shape
        rows_dropped = initial_shape[0] - final_shape[0]
        logger.info(f"Dropped {rows_dropped} rows containing missing values.")
        return df_cleaned
    except Exception as e:
        logger.error(f"Error during data cleaning: {str(e)}")
        raise e

