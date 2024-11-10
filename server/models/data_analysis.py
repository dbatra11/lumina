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
import numpy as np

def analyze_data(df):
    """
    Analyze the DataFrame and return insights, chart data, and a summary.
    Includes correlation matrix, histograms, scatter plots, clustering, feature importance, and future sales predictions.
    """
    logger = logging.getLogger(__name__)
    
    insights = {}
    charts = []
    summary = ""
    
    # Ensure DataFrame has numeric data for analysis
    numeric_df = df.select_dtypes(include=['number'])
    if numeric_df.empty:
        logger.warning("No numeric data available for analysis.")
        return insights, charts, summary

    # Detect target variable automatically
    target_variable = detect_target_variable(numeric_df)
    if not target_variable:
        logger.error("No suitable target variable found in the dataset.")
        raise ValueError("No suitable target variable found in the dataset.")
    logger.info(f"Detected target variable: {target_variable}")

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
        # Find the pair with the highest correlation excluding the target variable
        corr_matrix = numeric_df.drop(columns=[target_variable]).corr().abs()
        upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
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
        scaled_data = scaler.fit_transform(numeric_df.drop(columns=[target_variable]))
        kmeans = KMeans(n_clusters=3, random_state=42)
        clusters = kmeans.fit_predict(scaled_data)
        numeric_df['Cluster'] = clusters
        insights['clustering'] = {
            "labels": clusters.tolist()
            # 'cluster_centers' excluded as per user request
        }
        logger.info("Clustering analysis completed successfully.")

        # Scatter plot for clusters using the first two features (excluding target)
        plt.figure(figsize=(10,6))
        first_feature = numeric_df.columns[0]
        second_feature = numeric_df.columns[1]
        sns.scatterplot(x=first_feature, y=second_feature, hue='Cluster', palette='viridis', data=numeric_df)
        plt.title('K-Means Clustering')
        plt.xlabel(first_feature)
        plt.ylabel(second_feature)

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
        X = numeric_df.drop(columns=[target_variable, 'Cluster'])
        y = numeric_df[target_variable]
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

    # Future Sales Prediction using Prophet (Assuming there's a 'Date' or similar column)
    date_column = detect_date_column(df)
    if date_column and target_variable:
        try:
            sales_df = df[[date_column, target_variable]].rename(columns={date_column: 'ds', target_variable: 'y'})
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
            plt.close(fig1)
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode('utf-8')

            forecast_chart = {
                "type": "image",
                "title": f"{target_variable} Forecast for Next 30 Days",
                "image": image_base64
            }
            charts.append(forecast_chart)

            # Add forecast data to insights
            insights['forecast'] = forecast.tail(30)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_dict(orient='records')
            logger.info(f"{target_variable} forecast generated successfully.")
        except Exception as e:
            logger.error(f"Failed to generate {target_variable} forecast: {str(e)}")
            forecast_error_chart = {
                "type": "text",
                "title": f"{target_variable} Forecast",
                "text": f"Failed to generate {target_variable} forecast: {str(e)}"
            }
            charts.append(forecast_error_chart)
    else:
        logger.warning("No suitable date column found for forecasting or no target variable detected.")

    # Generate summary based on insights
    summary = generate_summary(insights, target_variable)
    
    return insights, charts, summary

def detect_target_variable(numeric_df):
    """
    Automatically detect the target variable from the numeric DataFrame.
    Criteria:
    - Select the numeric column with the highest variance.
    - Exclude columns with dates or times if any.
    """
    # Compute variance for each numeric column
    variances = numeric_df.var().sort_values(ascending=False)
    if variances.empty:
        return None
    # Select the column with the highest variance as the target
    target = variances.idxmax()
    return target

def detect_date_column(df):
    """
    Detect a date or datetime column in the DataFrame.
    """
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    return None

def generate_summary(insights, target_variable):
    """
    Generate a summary of conclusions based on the insights and target variable.
    """
    summary = []

    # Feature Importance
    if 'feature_importance' in insights:
        top_features = sorted(insights['feature_importance'].items(), key=lambda x: x[1], reverse=True)[:3]
        summary.append(f"The top features influencing {target_variable} are:")
        for feature, importance in top_features:
            summary.append(f"- {feature}: Importance Score of {importance:.2f}")
    
    # Correlation Matrix
    if 'correlation_matrix' in insights:
        strong_corr = []
        for feature, correlations in insights['correlation_matrix'].items():
            for other_feature, corr_value in correlations.items():
                if feature != other_feature and abs(corr_value) > 0.7:
                    # To avoid duplicate pairs, ensure feature < other_feature
                    if feature < other_feature:
                        strong_corr.append((feature, other_feature, corr_value))
        # Remove duplicate pairs
        unique_strong_corr = []
        seen = set()
        for feat1, feat2, corr in strong_corr:
            if (feat1, feat2) not in seen:
                unique_strong_corr.append((feat1, feat2, corr))
                seen.add((feat1, feat2))
        if unique_strong_corr:
            summary.append(f"Strong correlations detected between the following feature pairs:")
            for feat1, feat2, corr in unique_strong_corr:
                summary.append(f"- {feat1} and {feat2}: Correlation of {corr:.2f}")
    
    # Clustering
    if 'clustering' in insights:
        labels = insights['clustering']['labels']
        num_clusters = len(set(labels))
        cluster_counts = pd.Series(labels).value_counts().to_dict()
        summary.append(f"K-Means Clustering identified {num_clusters} distinct clusters:")
        for cluster, count in sorted(cluster_counts.items()):
            summary.append(f"- Cluster {cluster}: {count} data points")
    
    # Forecast
    if 'forecast' in insights and len(insights['forecast']) > 0:
        last_forecast = insights['forecast'][-1]
        predicted_revenue = last_forecast['yhat']
        predicted_date = pd.to_datetime(last_forecast['ds'])
        summary.append(f"The {target_variable} forecast for {predicted_date.strftime('%Y-%m-%d')} is estimated to be {predicted_revenue:.2f}.")
    
    # Join the summary lines into a paragraph
    summary_text = " ".join(summary)
    
    # Log the summary
    logger = logging.getLogger(__name__)
    logger.info(f"Generated Summary: {summary_text}")
    
    return summary_text

