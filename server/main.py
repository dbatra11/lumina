from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
from models import  ml_predict, data_analysis
from utils import data_cleaning
import os
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/api/clean', methods=['POST'])
def clean_data():
    file = request.files['file']
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Determine file extension and read accordingly
    if filename.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    elif filename.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif filename.endswith('.json'):
        df = pd.read_json(file_path)
    else:
        return jsonify({"error": "Unsupported file type"}), 400
    # Clean the data
    cleaned_df = data_cleaning.clean(df)

    # Save the cleaned data in the same format
    cleaned_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'cleaned_' + filename)
    if filename.endswith('.xlsx'):
        cleaned_df.to_excel(cleaned_file_path, index=False)
    elif filename.endswith('.csv'):
        cleaned_df.to_csv(cleaned_file_path, index=False)
    elif filename.endswith('.json'):
        cleaned_df.to_json(cleaned_file_path, orient='records', indent=2)
    @after_this_request
    def remove_file(response):
        try:
            os.remove(file_path)
            os.remove(cleaned_file_path)
        except Exception as e:
            app.logger.error("Error removing or cleaning up files: %s", e)
        return response

    return send_file(cleaned_file_path, as_attachment=True)

@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    file = request.files['file']
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Determine file extension and read accordingly
    if filename.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    elif filename.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif filename.endswith('.json'):
        df = pd.read_json(file_path)
    else:
        return jsonify({"error": "Unsupported file type"}), 400

    # Analyze the data
    insights = data_analysis.analyze(df)
    @after_this_request
    def remove_file(response):
        try:
            os.remove(file_path)
        except Exception as e:
            app.logger.error("Error removing or cleaning up files: %s", e)
        return response

    return jsonify(insights)

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.get_json()
    predictions = ml_predict.predict_future(data)
    return jsonify(predictions)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
