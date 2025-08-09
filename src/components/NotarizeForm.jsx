import { useState } from 'react';

export default function NotarizeForm() {
  const [file, setFile] = useState(null);
  const [hash, setHash] = useState('');

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setFile(file);
    
    // Generate hash
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    
    setHash(hashHex);
  };

  return (
    <div className="form-container">
      <input type="file" onChange={handleUpload} />
      {file && <p>File: {file.name}</p>}
      {hash && (
        <div className="hash-result">
          <p>SHA-256 Hash:</p>
          <code>{hash}</code>
        </div>
      )}
    </div>
  );
}
