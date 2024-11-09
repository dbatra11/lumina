# backend/utils/data_cleaning.py

import pandas as pd
import logging

def clean(df):
    """
    Perform comprehensive data cleaning:
    - Remove duplicate rows
    - Handle missing values
    - Strip whitespace from string columns
    - Convert numerical columns to numeric types, coercing errors
    - Drop or handle columns with excessive non-numeric data
    """
    logger = logging.getLogger(__name__)

    # Remove duplicate rows
    initial_shape = df.shape
    df = df.drop_duplicates()
    logger.info(f"Dropped {initial_shape[0] - df.shape[0]} duplicate rows.")

    # Handle missing values
    # For numerical columns, fill with mean
    num_cols = df.select_dtypes(include=['number']).columns
    df[num_cols] = df[num_cols].fillna(df[num_cols].mean())
    logger.info(f"Filled missing values in numerical columns with mean.")

    # For categorical columns, fill with mode
    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    if not df[cat_cols].empty:
        df[cat_cols] = df[cat_cols].fillna(df[cat_cols].mode().iloc[0])
        logger.info(f"Filled missing values in categorical columns with mode.")

    # Strip whitespace from string columns
    if not df[cat_cols].empty:
        df[cat_cols] = df[cat_cols].apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        logger.info(f"Stripped whitespace from categorical columns.")

    # Convert numerical columns to numeric types, coercing errors
    for col in num_cols:
        original_non_numeric = df[col].dtype
        df[col] = pd.to_numeric(df[col], errors='coerce')
        num_non_numeric = df[col].isna().sum()
        if num_non_numeric > 0:
            logger.warning(f"Column '{col}' had {num_non_numeric} non-numeric values converted to NaN.")
            # Decide whether to fill NaN with mean or drop the column
            # Here, we fill NaN with mean
            df[col] = df[col].fillna(df[col].mean())
            logger.info(f"Filled NaN in column '{col}' with mean value.")

    # Drop columns that are entirely non-numeric after attempted conversion
    # Identify columns that were numeric but are now entirely NaN
    problematic_cols = []
    for col in num_cols:
        if df[col].isna().all():
            problematic_cols.append(col)

    if problematic_cols:
        df = df.drop(columns=problematic_cols)
        logger.warning(f"Dropped columns with all non-numeric data: {problematic_cols}")

    # Final check for any remaining NaN values
    remaining_nans = df.isna().sum().sum()
    if remaining_nans > 0:
        logger.warning(f"DataFrame still contains {remaining_nans} NaN values after cleaning.")

    return df
