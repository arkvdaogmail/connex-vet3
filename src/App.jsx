import React, { useState, useRef } from 'react';

export default function App() {
  const [account, setAccount] = useState(null);
  const [file, setFile] = useState(null);
  const [hash, setHash] = useState('');
  const fileInputRef = useRef(null);

  const connectWallet = async () => {
    try {
      // Use the wallet provider from your original working code
      if (typeof window.vechain !== 'undefined' || typeof window.sync2 !== 'undefined') {
        const provider = window.vechain || window.sync2;
        const accounts = await provider.request({ method: 'eth_requestAccounts' });
        
        if (accounts.length > 0) {
          setAccount(accounts[0]);
          alert(`Wallet connected: ${accounts[0]}`);
        }
      } else {
        alert('No VeChain wallet detected! Install Sync2 or VeWorld');
      }
    } catch (error) {
      console.error('Connection failed:', error);
      alert(`Connection failed: ${error.message}`);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setFile(file);
    
    // Generate SHA-256 hash
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    
    setHash(hashHex);
    alert(`File hashed successfully!`);
  };

  return (
    <div style={{ 
      padding: '20px', 
      fontFamily: 'Arial', 
      maxWidth: '600px', 
      margin: '0 auto',
      textAlign: 'center'
    }}>
      <h1>VeChain Notary</h1>
      
      {!account ? (
        <button 
          onClick={connectWallet}
          style={{
            padding: '10px 20px',
            background: '#2a5ada',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          Connect Wallet
        </button>
      ) : (
        <div>
          <p>Connected: {account.slice(0, 6)}...{account.slice(-4)}</p>
          
          <input 
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
          <button
            onClick={() => fileInputRef.current.click()}
            style={{
              padding: '10px 20px',
              background: '#2a5ada',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              marginTop: '20px'
            }}
          >
            Choose File
          </button>
          
          {file && <p style={{ marginTop: '15px' }}>Selected: {file.name}</p>}
          {hash && (
            <div style={{ 
              marginTop: '20px',
              padding: '15px',
              background: '#f5f5f5',
              borderRadius: '5px',
              textAlign: 'left'
            }}>
              <p>Document Hash:</p>
              <code style={{
                wordBreak: 'break-all',
                display: 'block',
                marginTop: '10px',
                padding: '10px',
                background: 'white'
              }}>
                {hash}
              </code>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
