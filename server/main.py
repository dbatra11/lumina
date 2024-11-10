# backend/main.py

import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend

from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
from models import ml_train, ml_predict, analyze_data
from utils import data_cleaning
import os
import pandas as pd
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

def convert_timestamps(obj):
    """
    Recursively convert pandas Timestamp objects to strings and handle NaT.
    """
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif pd.isna(obj):
        return None
    elif isinstance(obj, dict):
        return {k: convert_timestamps(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_timestamps(item) for item in obj]
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
            df = pd.read_csv(file_path, encoding=encoding)
        elif filename.endswith('.json'):
            # For JSON, attempt to detect encoding
            encoding, confidence = detect_file_encoding(file_path)
            if not encoding:
                logger.warning("Failed to detect file encoding. Defaulting to 'utf-8'.")
                encoding = 'utf-8'
            logger.info(f"Detected file encoding: {encoding} with confidence {confidence}")
            df = pd.read_json(file_path, encoding=encoding)
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

    @after_this_request
    def remove_file(response):
        try:
            os.remove(file_path)
            logger.info(f"Removed uploaded file {file_path}")
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {str(e)}")
        return response

    # Return the JSON response with insights, charts, and summary
    return jsonify({
        "insights": insights,
        "charts": charts,
        "summary": summary
    })

# Similarly, update the /api/clean endpoint if needed
# ...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
