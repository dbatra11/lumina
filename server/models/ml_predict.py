import pandas as pd
import logging

def ml_predict(model, data):
    """
    Make predictions using the trained model.
    Expects data as a list of dictionaries where keys are feature names.
    Returns a list of predictions.
    """
    logger = logging.getLogger(__name__)
    df_new = pd.DataFrame(data)
    logger.info("Received prediction input data.")

    # Ensure all features are numeric (handle encoding if necessary)
    # Note: In production, you should apply the same preprocessing as in training

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
