// frontend/src/App.js

import React, { useState } from 'react';
import axios from 'axios';
import './App.css';
import { Bar, Line, Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

function App() {
  const [file, setFile] = useState(null);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [cleanedFileUrl, setCleanedFileUrl] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [charts, setCharts] = useState(null);
  const [loading, setLoading] = useState(false); // Loading state
  const [error, setError] = useState(null); // Error state

  // Handle file selection
  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
    // Reset previous results and errors
    setAnalysisResults(null);
    setCleanedFileUrl(null);
    setStatistics(null);
    setCharts(null);
    setError(null);
  };

  // Handle data cleaning
  const handleCleanData = async () => {
    if (!file) {
      alert('Please upload a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post('http://127.0.0.1:5000/api/clean', formData, {
        responseType: 'blob',
      });
      // Create a URL for the cleaned file
      const url = window.URL.createObjectURL(new Blob([response.data]));
      setCleanedFileUrl(url);
      alert('Data cleaned successfully!');
    } catch (error) {
      console.error('Error cleaning data:', error);
      if (error.response && error.response.data && error.response.data.error) {
        alert(`Failed to clean data: ${error.response.data.error}`);
      } else {
        alert('Failed to clean data.');
      }
    }
  };

  // Handle data analysis
  const handleAnalyzeData = async () => {
    if (!file) {
      alert('Please upload a file first.');
      return;
    }

    setLoading(true); // Start loading
    setError(null); // Reset previous errors
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post('http://127.0.0.1:5000/api/analyze', formData);

      console.log('Analysis Response:', response.data); // Log entire response
      console.log('Summary:', response.data.summary);    // Log summary specifically

      setAnalysisResults(response.data);
      setCharts(response.data.charts || []);
      setLoading(false); // Stop loading
      alert('Data analyzed successfully!');
    } catch (error) {
      console.error('Error analyzing data:', error);
      if (error.response && error.response.data && error.response.data.error) {
        setError(`Failed to analyze data: ${error.response.data.error}`);
        alert(`Failed to analyze data: ${error.response.data.error}`);
      } else {
        setError('Failed to analyze data.');
        alert('Failed to analyze data.');
      }
      setLoading(false); // Stop loading
    }
  };

  // Handle descriptive statistics
  const handleDescriptiveStatistics = async () => {
    if (!file) {
      alert('Please upload a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post('http://127.0.0.1:5000/api/descriptive_statistics', formData);
      setStatistics(response.data);
      alert('Descriptive statistics retrieved successfully!');
    } catch (error) {
      console.error('Error getting descriptive statistics:', error);
      if (error.response && error.response.data && error.response.data.error) {
        alert(`Failed to retrieve descriptive statistics: ${error.response.data.error}`);
      } else {
        alert('Failed to retrieve descriptive statistics.');
      }
    }
  };

  // Render formatted tables for insights and statistics
  const renderFormattedTable = (data) => {
    return (
      <div>
        {renderNestedTable(data)}
      </div>
    );
  };

  // Render individual table cells
  const renderCell = (value) => {
    if (typeof value === 'object' && value !== null) {
      return renderNestedTable(value);
    } else {
      return <span>{value !== null && value !== undefined ? value : 'N/A'}</span>;
    }
  };

  // Render nested tables for complex data structures
  const renderNestedTable = (data) => {
    if (Array.isArray(data)) {
      return (
        <table className="table table-bordered table-hover">
          <thead>
            <tr>
              <th>Index</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item, index) => (
              <tr key={index}>
                <td>{index + 1}</td>
                <td>{renderCell(item)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    } else {
      return (
        <table className="table table-bordered table-hover">
          <tbody>
            {Object.entries(data).map(([key, value], index) => (
              <tr key={index}>
                <th>{key}</th>
                <td>{renderCell(value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }
  };

  // Render insights with titles and formatted data
  const renderInsights = (insights) => {
    if (!insights || Object.keys(insights).length === 0) {
      console.log("No insights available or insights are empty:", insights);
      return <p>No insights available.</p>;
    }

    return (
      <div>
        {Object.entries(insights).map(([section, sectionInsights], index) => {
          // Skip 'labels' and 'cluster_centers' within 'clustering' section
          if (section === 'clustering') {
            const { labels, cluster_centers, ...restSectionInsights } = sectionInsights;
            return (
              <div key={index}>
                <h3>{section.replace(/_/g, ' ').toUpperCase()}</h3>
                {Object.keys(restSectionInsights).length > 0 && renderFormattedTable(restSectionInsights)}
              </div>
            );
          }
          return (
            <div key={index}>
              <h3>{section.replace(/_/g, ' ').toUpperCase()}</h3>
              {renderFormattedTable(sectionInsights)}
            </div>
          );
        })}
      </div>
    );
  };

  // Render summary with proper formatting
  const renderSummary = (summary) => {
    if (!summary) return null;

    // Split the summary into sections based on dashes
    const lines = summary.split(' - ');

    // The first part before the first dash
    const firstPart = lines.shift();

    // The remaining parts are list items
    const listItems = lines.map(item => item.trim());

    return (
      <div className="summary-results mb-4">
        <h3>Summary</h3>
        <p>{firstPart}</p>
        <ul>
          {listItems.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </div>
    );
  };

  // Generate chart data for Chart.js
  const generateChartData = (chartInfo) => {
    const { type, labels, datasets } = chartInfo;
    const data = {
      labels: labels,
      datasets: datasets.map((ds) => ({
        label: ds.label,
        data: ds.data,
        backgroundColor: ds.backgroundColor || 'rgba(75,192,192,0.4)',
        borderColor: ds.borderColor || 'rgba(75,192,192,1)',
        fill: ds.fill || false,
      })),
    };
    return { type, data };
  };

  // Render charts based on their type
  const renderCharts = () => {
    if (!charts || charts.length === 0) return <p>No charts available.</p>;

    return charts.map((chartInfo, index) => {
      const { type, title, image, text } = chartInfo;

      if (type === 'image') {
        return (
          <div key={index} className="mb-4">
            <h4>{title}</h4>
            <img src={`data:image/png;base64,${image}`} alt={title} className="img-fluid" />
          </div>
        );
      }

      if (type === 'text') {
        return (
          <div key={index} className="mb-4">
            <h4>{title}</h4>
            <p>{text}</p>
          </div>
        );
      }

      // Existing Chart.js rendering...
      const { labels, datasets } = chartInfo;
      const data = generateChartData(chartInfo);
      const options = {
        responsive: true,
        plugins: {
          legend: {
            position: 'top',
          },
          title: {
            display: !!title,
            text: title || '',
          },
        },
      };

      switch (type) {
        case 'bar':
          return <Bar key={index} data={data} options={options} />;
        case 'line':
          return <Line key={index} data={data} options={options} />;
        case 'pie':
          return <Pie key={index} data={data} options={options} />;
        default:
          return null;
      }
    });
  };

  // Render descriptive statistics
  const renderStatistics = () => {
    if (!statistics) return null;

    return (
      <div className="statistics-results mb-4">
        <h2>Descriptive Statistics</h2>
        <h3>Describe</h3>
        {renderFormattedTable(statistics.describe)}
        <h3>Mode</h3>
        {renderFormattedTable(statistics.mode)}
      </div>
    );
  };

  return (
    <div className="App container">
      <h1 className="mt-4 mb-4">Lumina Data Assistant</h1>
      
      {/* File Input */}
      <div className="mb-3">
        <input type="file" onChange={handleFileChange} className="form-control" />
      </div>

      {/* Action Buttons */}
      <div className="mb-3">
        <button onClick={handleCleanData} className="btn btn-primary me-2">Clean Data</button>
        <button onClick={handleAnalyzeData} className="btn btn-success me-2">Analyze Data</button>
        <button onClick={handleDescriptiveStatistics} className="btn btn-info">Get Descriptive Statistics</button>
      </div>

      {/* Loading Indicator */}
      {loading && (
        <div className="mb-4">
          <p>Loading...</p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="alert alert-danger mb-4" role="alert">
          {error}
        </div>
      )}

      {/* Cleaned File Download */}
      {cleanedFileUrl && (
        <div className="mb-4">
          <h2>Download Cleaned File</h2>
          <a href={cleanedFileUrl} download={file ? `cleaned_${file.name}` : 'cleaned_data'} className="btn btn-secondary">
            Download Cleaned Data
          </a>
        </div>
      )}

      {/* Analysis Results */}
      {analysisResults && (
        <div className="analysis-results mb-4">
          <h2>Analysis Results</h2>

          {/* Render Structured Insights */}
          {renderInsights(analysisResults.insights)}

          {/* Render Summary */}
          {analysisResults.summary && (
            renderSummary(analysisResults.summary)
          )}

          {/* Data Visualizations */}
          {charts && charts.length > 0 && (
            <div className="charts mt-4">
              <h3>Data Visualizations</h3>
              {renderCharts()}
            </div>
          )}
        </div>
      )}

      {/* Descriptive Statistics */}
      {statistics && (
        renderStatistics()
      )}
    </div>
  );
}

export default App;

