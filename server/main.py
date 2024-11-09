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

@app.route('/api/clean', methods=['POST'])
def clean_data_route():
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
        if filename.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif filename.endswith('.json'):
            df = pd.read_json(file_path)
        else:
            logger.warning(f"Unsupported file type: {filename}")
            return jsonify({"error": "Unsupported file type"}), 400
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

    # Save the cleaned data in the same format
    cleaned_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'cleaned_' + filename)
    try:
        if filename.endswith('.xlsx'):
            cleaned_df.to_excel(cleaned_file_path, index=False)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif filename.endswith('.csv'):
            cleaned_df.to_csv(cleaned_file_path, index=False)
            mimetype = 'text/csv'
        elif filename.endswith('.json'):
            cleaned_df.to_json(cleaned_file_path, orient='records', indent=2, date_format='iso')
            mimetype = 'application/json'
    except Exception as e:
        logger.error(f"Failed to save cleaned data for file {filename}: {str(e)}")
        return jsonify({"error": f"Failed to save cleaned data: {str(e)}"}), 500

    @after_this_request
    def remove_file(response):
        try:
            os.remove(file_path)
            logger.info(f"Removed uploaded file {file_path}")
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {str(e)}")
        return response

    return send_file(cleaned_file_path, as_attachment=True, mimetype=mimetype)

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
        if filename.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif filename.endswith('.json'):
            df = pd.read_json(file_path)
        else:
            logger.warning(f"Unsupported file type: {filename}")
            return jsonify({"error": "Unsupported file type"}), 400
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
        insights, charts = analyze_data(cleaned_df)
        logger.info(f"Data analysis successful for file {filename}.")
    except Exception as e:
        logger.error(f"Data analysis failed for file {filename}: {str(e)}")
        return jsonify({"error": f"Data analysis failed: {str(e)}"}), 500

    # Train the machine learning model
    try:
        model, score = ml_train(cleaned_df)
        trained_model = model
        model_score = score
        insights['model_accuracy'] = score
        logger.info(f"Model trained successfully with accuracy: {score}")

        # Save the model to disk
        joblib.dump(model, 'models/trained_model.joblib')
        logger.info("Trained model saved to disk.")
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

    return jsonify({"insights": insights, "charts": charts})

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
        if filename.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif filename.endswith('.json'):
            df = pd.read_json(file_path)
        else:
            logger.warning(f"Unsupported file type: {filename}")
            return jsonify({"error": "Unsupported file type"}), 400
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
