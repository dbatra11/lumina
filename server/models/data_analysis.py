# backend/models/data_analysis.py

import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd

def analyze_data(df):
    """
    Analyze the DataFrame and return insights and chart data.
    """
    insights = {}
    charts = []

    # Correlation Matrix Insight
    if df.select_dtypes(include=['number']).shape[1] > 1:
        corr = df.corr().to_dict()
        insights['correlation_matrix'] = corr

    # Histogram of first numerical column
    numerical_columns = df.select_dtypes(include=['number']).columns
    if len(numerical_columns) >= 1:
        first_num_col = numerical_columns[0]
        bins = pd.cut(df[first_num_col], bins=10).value_counts().sort_index()

        plt.figure(figsize=(10,6))
        plt.bar(bins.index.astype(str), bins.values, color='skyblue')
        plt.title(f'Histogram of {first_num_col}')
        plt.xlabel(first_num_col)
        plt.ylabel('Frequency')
        plt.xticks(rotation=45)

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')

        chart = {
            "type": "image",
            "title": f"Histogram of {first_num_col}",
            "image": image_base64
        }
        charts.append(chart)

    # Pie Chart of first categorical column
    categorical_columns = df.select_dtypes(include=['object', 'category']).columns
    if len(categorical_columns) >= 1:
        first_cat_col = categorical_columns[0]
        value_counts = df[first_cat_col].value_counts().head(5)

        plt.figure(figsize=(8,8))
        plt.pie(value_counts.values, labels=value_counts.index, autopct='%1.1f%%', startangle=140)
        plt.title(f'Distribution of {first_cat_col}')

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')

        chart = {
            "type": "image",
            "title": f"Distribution of {first_cat_col}",
            "image": image_base64
        }
        charts.append(chart)

    return insights, charts
