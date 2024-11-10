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
  const [selectedChart, setSelectedChart] = useState(null);
  const [loading, setLoading] = useState(false); 
  const [error, setError] = useState(null);
  const [showSection, setShowSection] = useState(''); 

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
    setAnalysisResults(null);
    setCleanedFileUrl(null);
    setStatistics(null);
    setCharts(null);
    setError(null);
  };

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

  const handleAnalyzeData = async () => {
    if (!file) {
      alert('Please upload a file first.');
      return;
    }

    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post('http://127.0.0.1:5000/api/analyze', formData);
      const data = typeof response.data === "string" ? JSON.parse(response.data) : response.data;

      setAnalysisResults(data);
      setCharts(data.charts || []);
      setLoading(false);
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
      setLoading(false);
    }
  };

  const handleDescriptiveStatistics = async () => {
    if (!file) {
      alert('Please upload a file first.');
      return;
    }

    setLoading(true);
    setError(null);
    setShowSection('statistics');

    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post('http://127.0.0.1:5000/api/descriptive_statistics', formData);
      setStatistics(response.data);
      setLoading(false);
      alert('Descriptive statistics retrieved successfully!');
    } catch (error) {
      console.error('Error getting descriptive statistics:', error);
      if (error.response && error.response.data && error.response.data.error) {
        alert(`Failed to retrieve descriptive statistics: ${error.response.data.error}`);
      } else {
        alert('Failed to retrieve descriptive statistics.');
      }
      setLoading(false);
    }
  };

  const renderSectionButton = (label, section) => (
    <button onClick={() => setShowSection(showSection === section ? '' : section)} className="btn btn-primary mb-2">
      {label}
    </button>
  );

  const renderFormattedSummary = (summary) => {
    const lines = summary.split(' - ');
    return (
      <div>
        <p>{lines[0]}</p>
        <ul>
          {lines.slice(1).map((line, index) => (
            <li key={index}>{line.trim()}</li>
          ))}
        </ul>
      </div>
    );
  };

  const renderCorrelationMatrix = (matrix) => (
    <table className="table table-bordered table-hover">
      <thead>
        <tr>
          <th>Variable</th>
          {Object.keys(matrix).map((key) => (
            <th key={key}>{key}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {Object.entries(matrix).map(([rowKey, rowValues], rowIndex) => (
          <tr key={rowIndex}>
            <th>{rowKey}</th>
            {Object.values(rowValues).map((value, colIndex) => (
              <td key={colIndex}>{value}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );

  const renderFeatureImportance = (featureImportance) => (
    <table className="table table-bordered table-hover">
      <thead>
        <tr>
          <th>Feature</th>
          <th>Importance Score</th>
        </tr>
      </thead>
      <tbody>
        {Object.entries(featureImportance).map(([feature, importance], index) => (
          <tr key={index}>
            <td>{feature}</td>
            <td>{importance}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  const renderFormattedInsights = (insights) => {
    if (!insights || typeof insights !== 'object') return <p>No insights available.</p>;

    const filteredInsights = { ...insights };
    delete filteredInsights.clustering?.labels;

    return (
      <div>
        {filteredInsights.correlation_matrix && (
          <div className="mb-4">
            <h4>Correlation Matrix</h4>
            {renderCorrelationMatrix(filteredInsights.correlation_matrix)}
          </div>
        )}
        {filteredInsights.feature_importance && (
          <div className="mb-4">
            <h4>Feature Importance</h4>
            {renderFeatureImportance(filteredInsights.feature_importance)}
          </div>
        )}
        {filteredInsights.model_accuracy && (
          <div className="mb-4">
            <h4>Model Accuracy</h4>
            <p>{filteredInsights.model_accuracy}</p>
          </div>
        )}
      </div>
    );
  };

  const renderDescriptiveStatistics = (statistics) => {
    if (!statistics || !statistics.describe) return <p>No descriptive statistics available.</p>;

    return (
      <table className="table table-bordered table-hover">
        <thead>
          <tr>
            <th>Variable</th>
            {Object.keys(statistics.describe[Object.keys(statistics.describe)[0]]).map((key) => (
              <th key={key}>{key}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.entries(statistics.describe).map(([variable, stats], index) => (
            <tr key={index}>
              <th>{variable}</th>
              {Object.values(stats).map((value, idx) => (
                <td key={idx}>{value !== null ? value : 'N/A'}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  const renderCharts = () => {
    if (!charts || charts.length === 0) return <p>No charts available.</p>;

    return (
      <div>
        <h4>Select a Chart</h4>
        <select onChange={(e) => setSelectedChart(e.target.value)} className="form-select mb-4">
          <option value="">--Select Chart--</option>
          {charts.map((chart, index) => (
            <option key={index} value={index}>
              {chart.title || `Chart ${index + 1}`}
            </option>
          ))}
        </select>
        {selectedChart !== null && renderSelectedChart()}
      </div>
    );
  };

  const renderSelectedChart = () => {
    const chartInfo = charts[selectedChart];
    if (!chartInfo) return null;

    const { type, title, image, text } = chartInfo;
    if (type === 'image') {
      return (
        <div className="mb-4">
          <h4>{title}</h4>
          <img src={`data:image/png;base64,${image}`} alt={title} className="img-fluid" />
        </div>
      );
    }

    if (type === 'text') {
      return (
        <div className="mb-4">
          <h4>{title}</h4>
          <p>{text}</p>
        </div>
      );
    }

    const data = {
      labels: chartInfo.labels,
      datasets: chartInfo.datasets.map((ds) => ({
        label: ds.label,
        data: ds.data,
        backgroundColor: ds.backgroundColor || 'rgba(75,192,192,0.4)',
        borderColor: ds.borderColor || 'rgba(75,192,192,1)',
        fill: ds.fill || false,
      })),
    };
    const options = {
      responsive: true,
      plugins: {
        legend: { position: 'top' },
        title: { display: !!title, text: title || '' },
      },
    };

    switch (type) {
      case 'bar':
        return <Bar data={data} options={options} />;
      case 'line':
        return <Line data={data} options={options} />;
      case 'pie':
        return <Pie data={data} options={options} />;
      default:
        return null;
    }
  };

  return (
    <div className="App container">
      <h1 className="mt-4 mb-4">Lumina Data Assistant</h1>
      
      <div className="mb-3">
        <input type="file" onChange={handleFileChange} className="form-control" />
      </div>

      <div className="mb-3">
        <button onClick={handleCleanData} className="btn btn-primary me-2">Clean Data</button>
        <button onClick={handleAnalyzeData} className="btn btn-success me-2">Analyze Data</button>
        <button onClick={handleDescriptiveStatistics} className="btn btn-info">Get Descriptive Statistics</button>
      </div>

      {loading && <div className="mb-4"><p>Loading...</p></div>}
      {error && <div className="alert alert-danger mb-4" role="alert">{error}</div>}

      {cleanedFileUrl && (
        <div className="mb-4">
          <h2>Download Cleaned File</h2>
          <a href={cleanedFileUrl} download={file ? `cleaned_${file.name}` : 'cleaned_data'} className="btn btn-secondary">
            Download Cleaned Data
          </a>
        </div>
      )}

      {analysisResults && (
        <div className="analysis-options">
          {renderSectionButton("Show Summary", "summary")}
          {renderSectionButton("Show Insights", "insights")}
          {renderSectionButton("Show Charts", "charts")}
        </div>
      )}

      {showSection === "summary" && analysisResults.summary && (
        <div className="summary-results mb-4">
          <h3>Summary</h3>
          {renderFormattedSummary(analysisResults.summary)}
        </div>
      )}

      {showSection === "insights" && analysisResults.insights && (
        <div className="insights-results mb-4">
          <h3>Insights</h3>
          {renderFormattedInsights(analysisResults.insights)}
        </div>
      )}

      {showSection === "charts" && renderCharts()}
      
      {showSection === "statistics" && statistics && (
        <div className="statistics-results mb-4">
          <h2>Descriptive Statistics</h2>
          {renderDescriptiveStatistics(statistics)}
        </div>
      )}
    </div>
  );
}

export default App;
