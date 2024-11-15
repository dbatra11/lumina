# backend/main.py

import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend

from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
from models import ml_train, ml_predict, analyze_data
from utils import data_cleaning
import os
import pandas as pd
import numpy as np
import json
from werkzeug.utils import secure_filename
import logging
import joblib
import chardet  # Import chardet for encoding detection

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Store trained model in memory for simplicity
trained_model = None
model_score = None

def replace_nan_with_none(data):
    if isinstance(data, dict):
        return {k: replace_nan_with_none(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_nan_with_none(item) for item in data]
    elif isinstance(data, float) and np.isnan(data):
        return None
    return data

def convert_timestamps(obj):
    """
    Recursively convert non-serializable objects to serializable ones.
    """
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif pd.isna(obj):
        return None
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return obj.to_list()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    elif isinstance(obj, dict):
        return {k: convert_timestamps(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_timestamps(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    else:
        return obj
    
def detect_file_encoding(file_path, num_bytes=10000):
    """
    Detect the encoding of a file using chardet.
    Reads up to num_bytes for detection.
    """
    with open(file_path, 'rb') as f:
        raw_data = f.read(num_bytes)
    result = chardet.detect(raw_data)
    encoding = result['encoding']
    confidence = result['confidence']
    return encoding, confidence

@app.route('/api/analyze', methods=['POST'])
def analyze_data_endpoint():
    global trained_model, model_score
    file = request.files.get('file')
    if not file:
        logger.warning("No file provided in /api/analyze request.")
        return jsonify({"error": "No file provided"}), 400
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    logger.info(f"Received file {filename} for analysis.")

    # Determine file extension and read accordingly
    try:
        encoding = None
        if filename.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif filename.endswith('.csv'):
            # Detect encoding
            encoding, confidence = detect_file_encoding(file_path)
            if not encoding:
                logger.warning("Failed to detect file encoding. Defaulting to 'utf-8'.")
                encoding = 'utf-8'
            logger.info(f"Detected file encoding: {encoding} with confidence {confidence}")

            # Check Pandas version for encoding_errors support
            pandas_version = pd.__version__
            major, minor, _ = map(int, pandas_version.split('.'))
            if major > 1 or (major == 1 and minor >= 4):
                # Use encoding_errors if supported
                df = pd.read_csv(file_path, encoding=encoding, encoding_errors='replace')
            else:
                # Use Python's open with errors='replace'
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    df = pd.read_csv(f)
        elif filename.endswith('.json'):
            # For JSON, attempt to detect encoding
            encoding, confidence = detect_file_encoding(file_path)
            if not encoding:
                logger.warning("Failed to detect file encoding. Defaulting to 'utf-8'.")
                encoding = 'utf-8'
            logger.info(f"Detected file encoding: {encoding} with confidence {confidence}")

            # Check Pandas version for encoding_errors support in read_json
            pandas_version = pd.__version__
            major, minor, _ = map(int, pandas_version.split('.'))
            if major > 1 or (major == 1 and minor >= 4):
                # Use encoding_errors if supported
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    df = pd.read_json(f, encoding_errors='replace')
            else:
                # Use Python's open with errors='replace'
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    data = f.read()
                df = pd.read_json(data)
        else:
            logger.warning(f"Unsupported file type: {filename}")
            return jsonify({"error": "Unsupported file type"}), 400
    except UnicodeDecodeError as ude:
        logger.error(f"Unicode decode error: {str(ude)}")
        return jsonify({"error": f"Failed to read file due to encoding issues: {str(ude)}"}), 400
    except Exception as e:
        logger.error(f"Failed to read file {filename}: {str(e)}")
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 400

    # Clean the data before analysis
    try:
        cleaned_df = data_cleaning.clean(df)
        logger.info(f"Data cleaning successful for analysis of file {filename}.")
    except Exception as e:
        logger.error(f"Data cleaning failed for analysis of file {filename}: {str(e)}")
        return jsonify({"error": f"Data cleaning failed: {str(e)}"}), 500

    # Analyze the data
    try:
        insights, charts, summary = analyze_data(cleaned_df)
        logger.info(f"Data analysis successful for file {filename}.")
    except ValueError as ve:
        logger.error(f"Data analysis failed for file {filename}: {str(ve)}")
        return jsonify({"error": f"Data analysis failed: {str(ve)}"}), 400
    except Exception as e:
        logger.error(f"Data analysis failed for file {filename}: {str(e)}")
        return jsonify({"error": f"Data analysis failed: {str(e)}"}), 500

    # Train the machine learning model
    try:
        model, score = ml_train(cleaned_df)
        trained_model = model
        model_score = score
        insights['model_accuracy'] = score
        logger.info(f"Model trained successfully with R^2 score: {score}")
    
        # Save the model to disk
        joblib.dump(model, 'models/trained_model.joblib')
        logger.info("Trained model saved to disk.")
    except ValueError as ve:
        logger.error(f"Model training failed for file {filename}: {str(ve)}")
        return jsonify({"error": f"Model training failed: {str(ve)}"}), 400
    except Exception as e:
        logger.error(f"Model training failed for file {filename}: {str(e)}")
        return jsonify({"error": f"Model training failed: {str(e)}"}), 500
    response_data = {
        "insights": replace_nan_with_none(insights),
        "charts": replace_nan_with_none(charts),
        "summary": replace_nan_with_none(summary)
    }

    @after_this_request
    def remove_file(response):
        try:
            os.remove(file_path)
            logger.info(f"Removed uploaded file {file_path}")
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {str(e)}")
        return response

    # Return the JSON response with insights, charts, and summary
    return jsonify(response_data)

@app.route('/api/predict', methods=['POST'])
def predict_endpoint():
    global trained_model
    if not trained_model:
        # Attempt to load the model from disk
        try:
            trained_model = joblib.load('models/trained_model.joblib')
            logger.info("Trained model loaded from disk.")
        except Exception as e:
            logger.error(f"No trained model available and failed to load from disk: {str(e)}")
            return jsonify({"error": "No trained model available. Please analyze data first."}), 400
    data = request.get_json()
    if not data:
        logger.warning("No data provided for prediction.")
        return jsonify({"error": "No data provided for prediction"}), 400
    try:
        predictions = ml_predict(trained_model, data)
        logger.info("Predictions made successfully.")
        return jsonify({"predictions": predictions})
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

@app.route('/api/descriptive_statistics', methods=['POST'])
def descriptive_statistics():
    file = request.files.get('file')
    if not file:
        logger.warning("No file provided in /api/descriptive_statistics request.")
        return jsonify({"error": "No file provided"}), 400
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    logger.info(f"Received file {filename} for descriptive statistics.")

    # Determine file extension and read accordingly
    try:
        encoding = None
        if filename.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif filename.endswith('.csv'):
            # Detect encoding
            encoding, confidence = detect_file_encoding(file_path)
            if not encoding:
                logger.warning("Failed to detect file encoding. Defaulting to 'utf-8'.")
                encoding = 'utf-8'
            logger.info(f"Detected file encoding: {encoding} with confidence {confidence}")

            # Check Pandas version for encoding_errors support
            pandas_version = pd.__version__
            major, minor, _ = map(int, pandas_version.split('.'))
            if major > 1 or (major == 1 and minor >= 4):
                # Use encoding_errors if supported
                df = pd.read_csv(file_path, encoding=encoding, encoding_errors='replace')
            else:
                # Use Python's open with errors='replace'
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    df = pd.read_csv(f)
        elif filename.endswith('.json'):
            # For JSON, attempt to detect encoding
            encoding, confidence = detect_file_encoding(file_path)
            if not encoding:
                logger.warning("Failed to detect file encoding. Defaulting to 'utf-8'.")
                encoding = 'utf-8'
            logger.info(f"Detected file encoding: {encoding} with confidence {confidence}")

            # Check Pandas version for encoding_errors support in read_json
            pandas_version = pd.__version__
            major, minor, _ = map(int, pandas_version.split('.'))
            if major > 1 or (major == 1 and minor >= 4):
                # Use encoding_errors if supported
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    df = pd.read_json(f, encoding_errors='replace')
            else:
                # Use Python's open with errors='replace'
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    data = f.read()
                df = pd.read_json(data)
        else:
            logger.warning(f"Unsupported file type: {filename}")
            return jsonify({"error": "Unsupported file type"}), 400
    except UnicodeDecodeError as ude:
        logger.error(f"Unicode decode error: {str(ude)}")
        return jsonify({"error": f"Failed to read file due to encoding issues: {str(ude)}"}), 400
    except Exception as e:
        logger.error(f"Failed to read file {filename}: {str(e)}")
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 400

    # Clean the data before generating statistics
    try:
        cleaned_df = data_cleaning.clean(df)
        logger.info(f"Data cleaning successful for descriptive statistics of file {filename}.")
    except Exception as e:
        logger.error(f"Data cleaning failed for descriptive statistics of file {filename}: {str(e)}")
        return jsonify({"error": f"Data cleaning failed: {str(e)}"}), 500

    # Convert datetime columns to string to avoid serialization issues
    datetime_cols = cleaned_df.select_dtypes(include=['datetime', 'datetime64']).columns
    for col in datetime_cols:
        cleaned_df[col] = cleaned_df[col].astype(str)

    # Generate descriptive statistics
    try:
        describe_stats = cleaned_df.describe(include='all').to_dict()
        mode_stats = cleaned_df.mode().iloc[0].to_dict()
        combined_stats = {
            "describe": convert_timestamps(describe_stats),
            "mode": convert_timestamps(mode_stats)
        }
        logger.info(f"Descriptive statistics generated successfully for file {filename}.")
    except Exception as e:
        logger.error(f"Failed to generate descriptive statistics for file {filename}: {str(e)}")
        return jsonify({"error": f"Failed to generate descriptive statistics: {str(e)}"}), 500

    @after_this_request
    def remove_file(response):
        try:
            os.remove(file_path)
            logger.info(f"Removed uploaded file {file_path}")
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {str(e)}")
        return response

    # Return the JSON response
    return jsonify(combined_stats)

@app.route('/api/clean', methods=['POST'])
def clean_data_endpoint():
    file = request.files.get('file')
    if not file:
        logger.warning("No file provided in /api/clean request.")
        return jsonify({"error": "No file provided"}), 400
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    logger.info(f"Received file {filename} for cleaning.")

    # Determine file extension and read accordingly
    try:
        encoding = None
        if filename.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif filename.endswith('.csv'):
            # Detect encoding
            encoding, confidence = detect_file_encoding(file_path)
            if not encoding:
                logger.warning("Failed to detect file encoding. Defaulting to 'utf-8'.")
                encoding = 'utf-8'
            logger.info(f"Detected file encoding: {encoding} with confidence {confidence}")

            # Check Pandas version for encoding_errors support
            pandas_version = pd.__version__
            major, minor, _ = map(int, pandas_version.split('.'))
            if major > 1 or (major == 1 and minor >= 4):
                # Use encoding_errors if supported
                df = pd.read_csv(file_path, encoding=encoding, encoding_errors='replace')
            else:
                # Use Python's open with errors='replace'
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    df = pd.read_csv(f)
        elif filename.endswith('.json'):
            # For JSON, attempt to detect encoding
            encoding, confidence = detect_file_encoding(file_path)
            if not encoding:
                logger.warning("Failed to detect file encoding. Defaulting to 'utf-8'.")
                encoding = 'utf-8'
            logger.info(f"Detected file encoding: {encoding} with confidence {confidence}")

            # Check Pandas version for encoding_errors support in read_json
            pandas_version = pd.__version__
            major, minor, _ = map(int, pandas_version.split('.'))
            if major > 1 or (major == 1 and minor >= 4):
                # Use encoding_errors if supported
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    df = pd.read_json(f, encoding_errors='replace')
            else:
                # Use Python's open with errors='replace'
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    data = f.read()
                df = pd.read_json(data)
        else:
            logger.warning(f"Unsupported file type: {filename}")
            return jsonify({"error": "Unsupported file type"}), 400
    except UnicodeDecodeError as ude:
        logger.error(f"Unicode decode error: {str(ude)}")
        return jsonify({"error": f"Failed to read file due to encoding issues: {str(ude)}"}), 400
    except Exception as e:
        logger.error(f"Failed to read file {filename}: {str(e)}")
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 400

    # Clean the data
    try:
        cleaned_df = data_cleaning.clean(df)
        logger.info(f"Data cleaning successful for file {filename}.")
    except Exception as e:
        logger.error(f"Data cleaning failed for file {filename}: {str(e)}")
        return jsonify({"error": f"Data cleaning failed: {str(e)}"}), 500

    # Save the cleaned data to a new file
    cleaned_filename = f"cleaned_{filename}"
    cleaned_file_path = os.path.join(app.config['UPLOAD_FOLDER'], cleaned_filename)
    try:
        if filename.endswith('.xlsx'):
            cleaned_df.to_excel(cleaned_file_path, index=False)
        elif filename.endswith('.csv'):
            cleaned_df.to_csv(cleaned_file_path, index=False, encoding='utf-8')
        elif filename.endswith('.json'):
            cleaned_df.to_json(cleaned_file_path, orient='records', date_format='iso')
        logger.info(f"Cleaned data saved as {cleaned_filename}.")
    except Exception as e:
        logger.error(f"Failed to save cleaned data: {str(e)}")
        return jsonify({"error": f"Failed to save cleaned data: {str(e)}"}), 500

    # Determine MIME type
    try:
        import mimetypes
        mimetype, _ = mimetypes.guess_type(cleaned_file_path)
        if not mimetype:
            mimetype = 'application/octet-stream'
    except Exception:
        mimetype = 'application/octet-stream'

    @after_this_request
    def remove_file(response):
        try:
            os.remove(file_path)
            logger.info(f"Removed uploaded file {file_path}")
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {str(e)}")
        return response

    # Return the cleaned file as a downloadable attachment
    return send_file(cleaned_file_path, as_attachment=True, mimetype=mimetype)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)