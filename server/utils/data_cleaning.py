# backend/utils/data_cleaning.py

import pandas as pd
import logging

def clean(df):
    """
    Clean the DataFrame by dropping categorical variables, handling missing values,
    and removing constant columns.
    """
    logger = logging.getLogger(__name__)
    
    # Drop categorical columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    if len(categorical_cols) > 0:
        df = df.drop(columns=categorical_cols)
        logger.info(f"Dropped categorical columns: {list(categorical_cols)}")
    
    # Handle missing values - fill numerical NaNs with mean
    numerical_cols = df.select_dtypes(include=['number']).columns
    if len(numerical_cols) > 0:
        df[numerical_cols] = df[numerical_cols].fillna(df[numerical_cols].mean())
        logger.info("Filled missing numerical values with column means.")
    
    # Optionally, drop columns with constant values as they don't provide useful information
    constant_cols = [col for col in df.columns if df[col].nunique() <= 1]
    if len(constant_cols) > 0:
        df = df.drop(columns=constant_cols)
        logger.info(f"Dropped constant columns: {constant_cols}")
    
    return df
