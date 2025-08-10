async function notarize() {
    const fileInput = document.getElementById('fileInput');
    const resultDiv = document.getElementById('result');
    resultDiv.innerText = '';
    
    if (!fileInput.files.length) {
        resultDiv.innerText = 'Please select a file';
        return;
    }

    const file = fileInput.files[0];
    const reader = new FileReader();

    reader.onload = async function(e) {
        try {
            const buffer = e.target.result;
            const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
            
            // Determine backend URL
            const isLocal = window.location.hostname === 'localhost' || 
                            window.location.hostname === '127.0.0.1';
            const backendUrl = isLocal ? 
                'http://localhost:5002' : 
                'https://your-render-app.onrender.com';

            const response = await fetch(`${backendUrl}/notarize`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ content: hashHex })
            });

            // Check for JSON response
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Server returned non-JSON response');
            }

            const data = await response.json();
            if (response.ok) {
                resultDiv.innerText = `Success! TX ID: ${data.txId}`;
            } else {
                resultDiv.innerText = `Error: ${data.error}`;
            }
        } catch (error) {
            resultDiv.innerText = `Error: ${error.message}`;
            console.error(error);
        }
    };

    reader.readAsArrayBuffer(file);
}
