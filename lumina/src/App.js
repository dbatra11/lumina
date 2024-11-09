import React, { useState } from 'react';
import axios from 'axios';

function App() {
    const [data, setData] = useState("");
    const [result, setResult] = useState(null);

    const handleCleanData = async () => {
        try {
            const response = await axios.post('http://localhost:5000/api/clean', { data });
            setResult(response.data);
        } catch (error) {
            console.error("There was an error cleaning the data.", error);
        }
    };

    return (
        <div className="App">
            <h1>Lumina Data Assistant</h1>
            <textarea onChange={(e) => setData(e.target.value)} placeholder="Enter raw data..." />
            <button onClick={handleCleanData}>Clean Data</button>
            {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
        </div>
    );
}

export default App;