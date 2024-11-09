# backend/models/models.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeClassifier
import joblib
import logging

def ml_train(df):
    """
    Train a machine learning model based on the provided DataFrame.
    Assumes the last column is the target variable.
    Returns the trained model and its accuracy score.
    """
    logger = logging.getLogger(__name__)

    # Drop rows with missing values (already handled in cleaning)
    df = df.dropna()

    # Assume the last column is the target
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]

    # Handle categorical variables with one-hot encoding
    X = pd.get_dummies(X)
    logger.info("Applied one-hot encoding to categorical variables.")

    if y.dtype == 'object' or y.dtype.name == 'category':
        y = pd.factorize(y)[0]
        logger.info("Converted categorical target variable to numeric.")

    # Check for remaining non-numeric columns
    if not all(pd.api.types.is_numeric_dtype(dtype) for dtype in X.dtypes):
        logger.error("Not all features are numeric after encoding.")
        raise ValueError("All features must be numeric after encoding.")

    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    logger.info(f"Split data into training and testing sets with test size 20%.")

    # Choose model based on target type
    if pd.api.types.is_numeric_dtype(y):
        model = LinearRegression()
        logger.info("Initialized Linear Regression model for numeric target.")
    else:
        model = DecisionTreeClassifier()
        logger.info("Initialized Decision Tree Classifier model for categorical target.")

    # Train the model
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    logger.info(f"Model trained with score: {score}")

    return model, score

def ml_predict(model, data):
    """
    Make predictions using the trained model.
    Expects data as a list of dictionaries where keys are feature names.
    Returns a list of predictions.
    """
    logger = logging.getLogger(__name__)
    df_new = pd.DataFrame(data)
    df_new = pd.get_dummies(df_new)
    logger.info("Applied one-hot encoding to prediction input data.")

    # Align the new data with training data
    if hasattr(model, 'feature_names_in_'):
        model_features = model.feature_names_in_
        for feature in model_features:
            if feature not in df_new.columns:
                df_new[feature] = 0
                logger.warning(f"Feature '{feature}' missing in prediction input. Added with default value 0.")
        df_new = df_new[model_features]
        logger.info("Aligned prediction input features with training features.")
    else:
        logger.warning("Model does not have 'feature_names_in_' attribute. Proceeding without alignment.")

    # Check for non-numeric columns
    if not all(pd.api.types.is_numeric_dtype(dtype) for dtype in df_new.dtypes):
        logger.error("Non-numeric data found in prediction input.")
        raise ValueError("All prediction input features must be numeric.")

    predictions = model.predict(df_new)
    logger.info("Predictions made successfully.")
    return predictions.tolist()
