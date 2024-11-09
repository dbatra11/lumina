import React, { useState } from 'react';
import axios from 'axios';
import { Button, Container, Form, Row, Col, ProgressBar, Spinner } from 'react-bootstrap';

function App() {
    const [file, setFile] = useState(null);
    const [result, setResult] = useState(null);
    const [downloadLink, setDownloadLink] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
        setResult(null);
        setDownloadLink(null);
        setProgress(0);
    };

    const handleCleanData = async () => {
        if (!file) {
            alert("Please select a file first.");
            return;
        }

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post('http://127.0.0.1:5000/api/clean', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                },
                responseType: 'blob',
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                    setProgress(percentCompleted);
                }
            });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            setDownloadLink(url);
        } catch (error) {
            console.error("There was an error cleaning the data.", error);
        } finally {
            setUploading(false);
        }
    };

    const handleAnalyzeData = async () => {
        if (!file) {
            alert("Please select a file first.");
            return;
        }

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post('http://127.0.0.1:5000/api/analyze', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
            setResult(response.data);
        } catch (error) {
            console.error("There was an error analyzing the data.", error);
        } finally {
            setUploading(false);
        }
    };
    return (
        <Container className="App">
            <h1>Lumina Data Assistant</h1>
            <Row className="justify-content-md-center">
                <Col md="6">
                    <Form.Group controlId="formFile" className="mb-3">
                        <Form.Label>Select a file to clean or analyze</Form.Label>
                        <Form.Control type="file" onChange={handleFileChange} />
                    </Form.Group>
                    {uploading && <ProgressBar animated now={progress} label={`${progress}%`} className="mb-3" />}
                    <Button variant="primary" onClick={handleCleanData} className="me-2" disabled={uploading}>{uploading ? <Spinner animation="border" size="sm" /> : "Clean Data"}</Button>
                    <Button variant="secondary" onClick={handleAnalyzeData} disabled={uploading}>{uploading ? <Spinner animation="border" size="sm" /> : "Analyze Data"}</Button>
                </Col>
            </Row>
            {downloadLink && (
                <Row className="justify-content-md-center mt-4">
                    <Col md="8">
                        <a href={downloadLink} download="cleaned_data">Download Cleaned File</a>
                    </Col>
                </Row>
            )}
            {result && (
                <Row className="justify-content-md-center mt-4">
                    <Col md="8">
                        <pre>{JSON.stringify(result, null, 2)}</pre>
                    </Col>
                </Row>
            )}
        </Container>
    );
}

export default App;