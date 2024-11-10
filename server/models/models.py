# backend/models/models.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import joblib
import logging

def ml_train(df):
    """
    Train a machine learning model based on the provided DataFrame.
    Assumes 'Revenue' is the target variable.
    Returns the trained model and its accuracy score.
    """
    logger = logging.getLogger(__name__)

    # Drop rows with missing values (already handled in cleaning)
    df = df.dropna()

    # Define target and features
    if 'Revenue' not in df.columns:
        logger.error("Target variable 'Revenue' not found in the dataset.")
        raise ValueError("Target variable 'Revenue' not found in the dataset.")

    X = df.drop(['Revenue'], axis=1)
    y = df['Revenue']

    # Ensure all features are numeric
    if not all(pd.api.types.is_numeric_dtype(dtype) for dtype in X.dtypes):
        X = X.apply(pd.to_numeric, errors='coerce').fillna(0)
        logger.info("Converted non-numeric features to numeric with NaN values filled.")

    # Ensure target variable is numeric
    if not pd.api.types.is_numeric_dtype(y):
        y = pd.to_numeric(y, errors='coerce').fillna(0)
        logger.info("Converted target variable 'Revenue' to numeric.")

    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    logger.info(f"Split data into training and testing sets with test size 20%.")

    # Initialize and train the model
    model = LinearRegression()
    logger.info("Initialized Linear Regression model.")
    model.fit(X_train, y_train)
    logger.info("Model training completed.")

    # Evaluate the model
    score = model.score(X_test, y_test)
    logger.info(f"Model R^2 Score: {score}")

    return model, score

def ml_predict(model, data):
    """
    Make predictions using the trained model.
    Expects data as a list of dictionaries where keys are feature names.
    Returns a list of predictions.
    """
    logger = logging.getLogger(__name__)
    df_new = pd.DataFrame(data)
    logger.info("Received prediction input data.")

    # Ensure all features are numeric
    if not all(pd.api.types.is_numeric_dtype(dtype) for dtype in df_new.dtypes):
        df_new = df_new.apply(pd.to_numeric, errors='coerce').fillna(0)
        logger.info("Converted non-numeric prediction input data to numeric with NaN values filled.")

    # Align the new data with training data
    if hasattr(model, 'feature_names_in_'):
        try:
            model_features = model.feature_names_in_
            for feature in model_features:
                if feature not in df_new.columns:
                    df_new[feature] = 0
                    logger.warning(f"Feature '{feature}' missing in prediction input. Added with default value 0.")
            df_new = df_new[model_features]
            logger.info("Aligned prediction input features with training features.")
        except AttributeError:
            logger.warning("Model does not have 'feature_names_in_' attribute. Proceeding without alignment.")

    predictions = model.predict(df_new)
    logger.info("Predictions made successfully.")
    return predictions.tolist()
