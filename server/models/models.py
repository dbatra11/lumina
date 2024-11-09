# backend/models/models.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeClassifier
import joblib

def ml_train(df):
    """
    Train a machine learning model based on the provided DataFrame.
    Assumes the last column is the target variable.
    Returns the trained model and its accuracy score.
    """
    # Drop rows with missing values
    df = df.dropna()

    # Assume the last column is the target
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]

    # Handle categorical variables
    X = pd.get_dummies(X)
    if y.dtype == 'object' or y.dtype.name == 'category':
        y = pd.factorize(y)[0]

    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Choose model based on target type
    if y.dtype == 'float' or y.dtype == 'int':
        model = LinearRegression()
    else:
        model = DecisionTreeClassifier()

    # Train the model
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)

    return model, score

def ml_predict(model, data):
    """
    Make predictions using the trained model.
    Expects data as a list of dictionaries where keys are feature names.
    Returns a list of predictions.
    """
    df_new = pd.DataFrame(data)
    df_new = pd.get_dummies(df_new)

    # Align the new data with training data
    model_features = model.feature_names_in_ if hasattr(model, 'feature_names_in_') else None
    if model_features is not None:
        for feature in model_features:
            if feature not in df_new.columns:
                df_new[feature] = 0
        df_new = df_new[model_features]

    predictions = model.predict(df_new)
    return predictions.tolist()
