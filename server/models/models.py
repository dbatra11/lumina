# backend/models/models.py

import logging
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import joblib

def ml_train(cleaned_df):
    """
    Train a Random Forest Regressor model on the cleaned DataFrame.
    Automatically detects the target variable.
    Returns the trained model and its R^2 score.
    """
    logger = logging.getLogger(__name__)

    # Detect target variable
    numeric_df = cleaned_df.select_dtypes(include=['number'])
    if numeric_df.empty:
        logger.error("No numeric data available for model training.")
        raise ValueError("No numeric data available for model training.")

    target_variable = detect_target_variable(numeric_df)
    if not target_variable:
        logger.error("No suitable target variable found for model training.")
        raise ValueError("No suitable target variable found for model training.")
    logger.info(f"Detected target variable for model training: {target_variable}")

    # Prepare features and target
    try:
        X = numeric_df.drop(columns=[target_variable])
        y = numeric_df[target_variable]
    except KeyError:
        logger.error(f"Target variable '{target_variable}' not found in the dataset.")
        raise ValueError(f"Target variable '{target_variable}' not found in the dataset.")

    # Split data into training and testing sets
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        logger.info("Split data into training and testing sets with test size 20%.")
    except Exception as e:
        logger.error(f"Failed to split data into training and testing sets: {str(e)}")
        raise ValueError(f"Failed to split data into training and testing sets: {str(e)}")

    # Initialize Random Forest Regressor model
    try:
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        logger.info("Initialized Random Forest Regressor model.")
    except Exception as e:
        logger.error(f"Failed to initialize Random Forest Regressor: {str(e)}")
        raise ValueError(f"Failed to initialize Random Forest Regressor: {str(e)}")

    # Model training
    try:
        rf.fit(X_train, y_train)
        logger.info("Model training completed.")
    except Exception as e:
        logger.error(f"Model training failed: {str(e)}")
        raise ValueError(f"Model training failed: {str(e)}")

    # Model evaluation
    try:
        y_pred = rf.predict(X_test)
        score = r2_score(y_test, y_pred)
        logger.info(f"Model R^2 Score: {score}")
    except Exception as e:
        logger.error(f"Failed to evaluate model: {str(e)}")
        raise ValueError(f"Failed to evaluate model: {str(e)}")

    return rf, score

def detect_target_variable(numeric_df):
    """
    Automatically detect the target variable from the numeric DataFrame.
    Criteria:
    - Select the numeric column with the highest variance.
    - Exclude columns that might represent features rather than targets.
    """
    # Compute variance for each numeric column
    variances = numeric_df.var().sort_values(ascending=False)
    if variances.empty:
        return None
    # Select the column with the highest variance as the target
    target = variances.idxmax()
    return target
