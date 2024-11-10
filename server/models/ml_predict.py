# backend/models/ml_predict.py

import pandas as pd
import joblib
import logging

def load_model(model_path='models/trained_model.joblib'):
    """
    Load the trained machine learning model from disk.
    """
    try:
        model = joblib.load(model_path)
        logging.info("Trained model loaded successfully.")
        return model
    except Exception as e:
        logging.error(f"Failed to load the trained model: {str(e)}")
        raise e

def predict_future(model, data):
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
