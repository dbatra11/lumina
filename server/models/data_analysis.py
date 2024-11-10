# backend/models/data_analysis.py

import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
from prophet import Prophet  # Ensure Prophet is installed
import logging
import seaborn as sns

def analyze_data(df):
    """
    Analyze the DataFrame and return insights and chart data.
    Includes correlation matrix, histograms, scatter plots, and future sales predictions.
    """
    logger = logging.getLogger(__name__)
    
    # Drop non-numerical columns
    df = df.select_dtypes(include=['number'])
    
    insights = {}
    charts = []

    # Correlation Matrix Insight
    if df.shape[1] > 1:
        corr = df.corr().to_dict()
        insights['correlation_matrix'] = corr

        # Heatmap for correlation matrix
        plt.figure(figsize=(12, 10))
        sns.heatmap(df.corr(), annot=True, cmap='coolwarm')
        plt.title('Correlation Heatmap')
        
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')

        heatmap_chart = {
            "type": "image",
            "title": "Correlation Heatmap",
            "image": image_base64
        }
        charts.append(heatmap_chart)

    # Histogram of numerical columns
    for col in df.columns:
        plt.figure(figsize=(10,6))
        plt.hist(df[col], bins=10, color='skyblue', edgecolor='black')
        plt.title(f'Histogram of {col}')
        plt.xlabel(col)
        plt.ylabel('Frequency')

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')

        histogram_chart = {
            "type": "image",
            "title": f"Histogram of {col}",
            "image": image_base64
        }
        charts.append(histogram_chart)

    # Scatter Plot between two highly correlated variables
    if df.shape[1] >= 2:
        col1, col2 = df.columns[0], df.columns[1]
        plt.figure(figsize=(10,6))
        plt.scatter(df[col1], df[col2], alpha=0.7, color='green')
        plt.title(f'Scatter Plot of {col1} vs {col2}')
        plt.xlabel(col1)
        plt.ylabel(col2)

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')

        scatter_chart = {
            "type": "image",
            "title": f"Scatter Plot of {col1} vs {col2}",
            "image": image_base64
        }
        charts.append(scatter_chart)

    # Future Sales Prediction using Prophet (Assuming 'Revenue' is the target and there's a 'Date' column)
    if 'Revenue' in df.columns and 'Date' in df.columns:
        try:
            sales_df = df[['Date', 'Revenue']].rename(columns={'Date': 'ds', 'Revenue': 'y'})
            sales_df['ds'] = pd.to_datetime(sales_df['ds'])
            model = Prophet()
            model.fit(sales_df)
            future = model.make_future_dataframe(periods=30)  # Predicting next 30 days
            forecast = model.predict(future)

            # Plot forecast
            fig1 = model.plot(forecast)
            buf = io.BytesIO()
            plt.tight_layout()
            fig1.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode('utf-8')

            forecast_chart = {
                "type": "image",
                "title": "Revenue Forecast for Next 30 Days",
                "image": image_base64
            }
            charts.append(forecast_chart)

            # Add forecast data to insights
            insights['forecast'] = forecast.tail(30)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_dict(orient='records')
            logger.info("Revenue forecast generated successfully.")
        except Exception as e:
            logger.error(f"Failed to generate revenue forecast: {str(e)}")
            # Optionally, you can include an error message in the charts
            forecast_error_chart = {
                "type": "text",
                "title": "Revenue Forecast",
                "text": f"Failed to generate revenue forecast: {str(e)}"
            }
            charts.append(forecast_error_chart)

    return insights, charts
