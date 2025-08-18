// src/DataImportExport.jsx
import { useRef, useState } from 'react';

export default function DataImportExport() {
  const fileRef = useRef();
  const [msg, setMsg] = useState('');

  const handleExport = () => {
    window.location = `${import.meta.env.VITE_API_URL}/api/export`;
  };

  const handleImport = async (e) => {
    e.preventDefault();
    const file = fileRef.current.files[0];
    if (!file) {
      setMsg('Select a CSV first');
      return;
    }
    setMsg('Importing…');

    const form = new FormData();
    form.append('file', file);

    const res = await fetch(`${import.meta.env.VITE_API_URL}/api/search/upload`, {
      method: 'POST',
      body: form,
    });
    if (!res.ok) {//For debugging
    const text = await res.text();
    console.error('Upload failed:', res.status, text);
  }

    setMsg(res.ok ? 'Import successful' : 'Import failed');
  };

  return (
    <div className="bauhaus-tool-content">
      <div className="tool-actions">
        <button
          onClick={handleExport}
          className="bauhaus-tool-button export-button"
        >
          <span>DOWNLOAD EXCEL</span>
          <div className="tool-button-accent blue"></div>
        </button>

        <form onSubmit={handleImport} className="import-form">
          <div className="file-input-group">
            <input 
              ref={fileRef} 
              type="file" 
              accept=".csv" 
              className="bauhaus-file-input" 
              id="csv-upload"
            />
            <label htmlFor="csv-upload" className="file-input-label">
              CHOOSE FILE
            </label>
          </div>
          <button
            type="submit"
            className="bauhaus-tool-button upload-button"
          >
            <span>UPLOAD CSV</span>
            <div className="tool-button-accent red"></div>
          </button>
        </form>
      </div>

      {msg && (
        <div className={`tool-message ${msg.includes('failed') ? 'error' : 'success'}`}>
          {msg.toUpperCase()}
        </div>
      )}
    </div>
  );
}