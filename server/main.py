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

@app.route('/api/clean', methods=['POST'])
def clean_data_route():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file provided"}), 400
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Determine file extension and read accordingly
    try:
        if filename.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif filename.endswith('.json'):
            df = pd.read_json(file_path)
        else:
            return jsonify({"error": "Unsupported file type"}), 400
    except Exception as e:
        logger.error(f"Failed to read file {filename}: {str(e)}")
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 400

    # Clean the data
    try:
        cleaned_df = data_cleaning.clean(df)
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
            cleaned_df.to_json(cleaned_file_path, orient='records', indent=2)
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
        return jsonify({"error": "No file provided"}), 400
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Determine file extension and read accordingly
    try:
        if filename.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif filename.endswith('.json'):
            df = pd.read_json(file_path)
        else:
            return jsonify({"error": "Unsupported file type"}), 400
    except Exception as e:
        logger.error(f"Failed to read file {filename}: {str(e)}")
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 400

    # Analyze the data
    try:
        insights, charts = analyze_data(df)
    except Exception as e:
        logger.error(f"Data analysis failed for file {filename}: {str(e)}")
        return jsonify({"error": f"Data analysis failed: {str(e)}"}), 500

    # Train the machine learning model
    try:
        model, score = ml_train(df)
        trained_model = model
        model_score = score
        insights['model_accuracy'] = score
        logger.info(f"Model trained successfully with accuracy: {score}")
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
        return jsonify({"error": "No trained model available. Please analyze data first."}), 400
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided for prediction"}), 400
    try:
        predictions = ml_predict(trained_model, data)
        logger.info(f"Predictions made successfully for input data.")
        return jsonify({"predictions": predictions})
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

@app.route('/api/descriptive_statistics', methods=['POST'])
def descriptive_statistics():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file provided"}), 400
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Determine file extension and read accordingly
    try:
        if filename.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif filename.endswith('.json'):
            df = pd.read_json(file_path)
        else:
            return jsonify({"error": "Unsupported file type"}), 400
    except Exception as e:
        logger.error(f"Failed to read file {filename}: {str(e)}")
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 400

    # Generate descriptive statistics
    try:
        descriptive_stats = df.describe(include='all').to_dict()
    except Exception as e:
        logger.error(f"Failed to generate descriptive statistics for file {filename}: {str(e)}")
        return jsonify({"error": f"Failed to generate descriptive statistics: {str(e)}"}), 500

    # Serialize with default=str to handle Timestamps
    try:
        descriptive_stats_json = json.dumps(descriptive_stats, indent=2, default=str)
    except TypeError as e:
        logger.error(f"Serialization error for descriptive statistics: {str(e)}")
        return jsonify({"error": f"Serialization error: {str(e)}"}), 500

    @after_this_request
    def remove_file(response):
        try:
            os.remove(file_path)
            logger.info(f"Removed uploaded file {file_path}")
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {str(e)}")
        return response

    # Return the JSON response
    return app.response_class(
        response=descriptive_stats_json,
        status=200,
        mimetype='application/json'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
