import React, { useState } from 'react';
import {  Row, Col} from 'react-bootstrap';
import axios from 'axios';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [cleanedFileUrl, setCleanedFileUrl] = useState(null);
  const [statistics, setStatistics] = useState(null);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleCleanData = async () => {
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post('http://localhost:5000/api/clean', formData, {
        responseType: 'blob',
      });
      // Create a URL for the cleaned file
      const url = window.URL.createObjectURL(new Blob([response.data]));
      setCleanedFileUrl(url);
    } catch (error) {
      console.error('Error cleaning data:', error);
    }
  };

  const handleAnalyzeData = async () => {
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post('http://localhost:5000/api/analyze', formData);
      setAnalysisResults(response.data);
    } catch (error) {
      console.error('Error analyzing data:', error);
    }
  };

  const handleDescriptiveStatistics = async () => {
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post('http://localhost:5000/api/descriptive_statistics', formData);
      setStatistics(response.data);
    } catch (error) {
      console.error('Error getting descriptive statistics:', error);
    }
  };

  return (
    <div className="App">
      <h1>Lumina Data Assistant</h1>
      <input type="file" onChange={handleFileChange} />
      <div>
        <button onClick={handleCleanData}>Clean Data</button>
        <button onClick={handleAnalyzeData}>Analyze Data</button>
        <button onClick={handleDescriptiveStatistics}>Get Descriptive Statistics</button>
      </div>

      {cleanedFileUrl && (
        <div>
          <h2>Download Cleaned File</h2>
          <a href={cleanedFileUrl} download={file ? `cleaned_${file.name}` : 'cleaned_data'}>Download Cleaned Data</a>
        </div>
      )}

    {analysisResults && (
                <Row className="justify-content-md-center mt-4">
                  <Col md="8">
                    <pre>{JSON.stringify(analysisResults, null, 2)}</pre>
                  </Col>
                </Row>       
            )}

      {statistics && (
        <div>
          <h2>Descriptive Statistics</h2>
          <pre>{JSON.stringify(statistics, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default App;