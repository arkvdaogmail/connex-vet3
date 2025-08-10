async function notarize() {
    const fileInput = document.getElementById('fileInput');
    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = '<span class="loading">Processing...</span>';
    
    if (!fileInput.files.length) {
        resultDiv.innerHTML = '<span class="error">Please select a file</span>';
        return;
    }

    try {
        // Calculate file hash
        const file = fileInput.files[0];
        const buffer = await file.arrayBuffer();
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

        // Send to backend
        const response = await fetch('/notarize', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ content: hashHex })
        });

        const data = await response.json();
        
        if (response.ok) {
            resultDiv.innerHTML = `
                <span class="success">Success!</span>
                <div class="tx-link">
                    TX ID: <a href="https://explore-testnet.vechain.org/transactions/${data.txId}" target="_blank">
                        ${data.txId.substring(0, 12)}...
                    </a>
                </div>
            `;
        } else {
            resultDiv.innerHTML = `<span class="error">Error: ${data.error || 'Unknown error'}</span>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<span class="error">Network Error: ${error.message}</span>`;
    }
}