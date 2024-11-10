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
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import numpy as np  # Imported NumPy directly

def analyze_data(df):
    """
    Analyze the DataFrame and return insights and chart data.
    Includes correlation matrix, histograms, scatter plots, clustering, feature importance, and future sales predictions.
    """
    logger = logging.getLogger(__name__)
    
    insights = {}
    charts = []

    # Ensure DataFrame has numeric data for analysis
    numeric_df = df.select_dtypes(include=['number'])
    if numeric_df.empty:
        logger.warning("No numeric data available for analysis.")
        return insights, charts

    # Correlation Matrix Insight
    if numeric_df.shape[1] > 1:
        corr = numeric_df.corr().to_dict()
        insights['correlation_matrix'] = corr

        # Heatmap for correlation matrix
        plt.figure(figsize=(12, 10))
        sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm')
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
    for col in numeric_df.columns:
        plt.figure(figsize=(10,6))
        plt.hist(numeric_df[col], bins=10, color='skyblue', edgecolor='black')
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
    if numeric_df.shape[1] >= 2:
        # Find the pair with the highest correlation
        corr_matrix = numeric_df.corr().abs()
        upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))  # Replaced pd.np with np
        max_corr = upper_tri.unstack().dropna().sort_values(ascending=False).head(1)
        if not max_corr.empty:
            col1, col2 = max_corr.index[0]
            plt.figure(figsize=(10,6))
            plt.scatter(numeric_df[col1], numeric_df[col2], alpha=0.7, color='green')
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

    # Clustering Analysis using K-Means
    try:
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(numeric_df)
        kmeans = KMeans(n_clusters=3, random_state=42)
        clusters = kmeans.fit_predict(scaled_data)
        numeric_df['Cluster'] = clusters
        insights['clustering'] = {
            "cluster_centers": kmeans.cluster_centers_.tolist(),
            "labels": clusters.tolist()
        }
        logger.info("Clustering analysis completed successfully.")

        # Scatter plot for clusters using the first two principal components
        plt.figure(figsize=(10,6))
        sns.scatterplot(x=numeric_df.columns[0], y=numeric_df.columns[1], hue='Cluster', palette='viridis', data=numeric_df)
        plt.title('K-Means Clustering')
        plt.xlabel(numeric_df.columns[0])
        plt.ylabel(numeric_df.columns[1])

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')

        cluster_chart = {
            "type": "image",
            "title": "K-Means Clustering",
            "image": image_base64
        }
        charts.append(cluster_chart)
    except Exception as e:
        logger.error(f"Clustering analysis failed: {str(e)}")
        cluster_error_chart = {
            "type": "text",
            "title": "Clustering Analysis",
            "text": f"Failed to perform clustering analysis: {str(e)}"
        }
        charts.append(cluster_error_chart)

    # Feature Importance using Random Forest
    try:
        if 'Revenue' in numeric_df.columns:
            X = numeric_df.drop('Revenue', axis=1)
            y = numeric_df['Revenue']
            rf = RandomForestRegressor(n_estimators=100, random_state=42)
            rf.fit(X, y)
            feature_importances = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False).to_dict()
            insights['feature_importance'] = feature_importances
            logger.info("Feature importance analysis completed successfully.")

            # Plot feature importances
            plt.figure(figsize=(10,6))
            sns.barplot(x=list(feature_importances.values()), y=list(feature_importances.keys()), palette='magma')
            plt.title('Feature Importance')
            plt.xlabel('Importance Score')
            plt.ylabel('Features')

            buf = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode('utf-8')

            feature_importance_chart = {
                "type": "image",
                "title": "Feature Importance",
                "image": image_base64
            }
            charts.append(feature_importance_chart)
    except Exception as e:
        logger.error(f"Feature importance analysis failed: {str(e)}")
        feature_importance_error_chart = {
            "type": "text",
            "title": "Feature Importance Analysis",
            "text": f"Failed to perform feature importance analysis: {str(e)}"
        }
        charts.append(feature_importance_error_chart)

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
