// frontend/src/App.js

import React, { useState } from 'react';
import { Row, Col } from 'react-bootstrap';
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

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
    // Reset previous results
    setAnalysisResults(null);
    setCleanedFileUrl(null);
    setStatistics(null);
    setCharts(null);
  };

  const handleCleanData = async () => {
    if (!file) {
      alert('Please upload a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post('http://localhost:5000/api/clean', formData, {
        responseType: 'blob',
      });
      // Create a URL for the cleaned file
      const url = window.URL.createObjectURL(new Blob([response.data]));
      setCleanedFileUrl(url);
      alert('Data cleaned successfully!');
    } catch (error) {
      console.error('Error cleaning data:', error);
      alert('Failed to clean data.');
    }
  };

  const handleAnalyzeData = async () => {
    if (!file) {
      alert('Please upload a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post('http://localhost:5000/api/analyze', formData);
      setAnalysisResults(response.data.insights);
      if (response.data.charts) {
        setCharts(response.data.charts);
      }
      alert('Data analyzed successfully!');
    } catch (error) {
      console.error('Error analyzing data:', error);
      if (error.response && error.response.data && error.response.data.error) {
        alert(`Failed to analyze data: ${error.response.data.error}`);
      } else {
        alert('Failed to analyze data.');
      }
    }
  };

  const handleDescriptiveStatistics = async () => {
    if (!file) {
      alert('Please upload a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post('http://localhost:5000/api/descriptive_statistics', formData);
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

  const renderFormattedTable = (data) => {
    return (
      <div>
        {renderNestedTable(data)}
      </div>
    );
  };

  const renderCell = (value) => {
    if (typeof value === 'object' && value !== null) {
      return renderNestedTable(value);
    } else {
      return <span>{value !== null ? value : 'N/A'}</span>;
    }
  };

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

  const renderCharts = () => {
    if (!charts) return null;

    return charts.map((chartInfo, index) => {
      const { type, title, image } = chartInfo;

      if (type === 'image') {
        return (
          <div key={index} className="mb-4">
            <h4>{title}</h4>
            <img src={`data:image/png;base64,${image}`} alt={title} className="img-fluid" />
          </div>
        );
      }

      // Existing Chart.js rendering...
      const { labels, datasets } = chartInfo;
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
      <div className="mb-3">
        <input type="file" onChange={handleFileChange} className="form-control" />
      </div>
      <div className="mb-3">
        <button onClick={handleCleanData} className="btn btn-primary me-2">Clean Data</button>
        <button onClick={handleAnalyzeData} className="btn btn-success me-2">Analyze Data</button>
        <button onClick={handleDescriptiveStatistics} className="btn btn-info">Get Descriptive Statistics</button>
      </div>

      {cleanedFileUrl && (
        <div className="mb-4">
          <h2>Download Cleaned File</h2>
          <a href={cleanedFileUrl} download={file ? `cleaned_${file.name}` : 'cleaned_data'} className="btn btn-secondary">
            Download Cleaned Data
          </a>
        </div>
      )}

      {analysisResults && (
        <div className="analysis-results mb-4">
          <h2>Analysis Results</h2>
          {renderFormattedTable(analysisResults)}
          {charts && (
            <div className="charts mt-4">
              <h3>Data Visualizations</h3>
              {renderCharts()}
            </div>
          )}
        </div>
      )}

      {statistics && (
        renderStatistics()
      )}
    </div>
  );
}

export default App;
