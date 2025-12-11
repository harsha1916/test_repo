// API Configuration Helper
// This file helps you set up your API key for the first time

(function() {
    const savedApiKey = localStorage.getItem('apiKey');
    
    if (!savedApiKey || savedApiKey === 'your-api-key-change-this') {
        console.log('%c⚠️ API Key Configuration Required', 'color: orange; font-size: 16px; font-weight: bold;');
        console.log('%cTo configure your API key:', 'color: blue; font-size: 14px;');
        console.log('%c1. Open your browser console (F12)', 'color: gray;');
        console.log('%c2. Run: localStorage.setItem("apiKey", "your-actual-api-key")', 'color: gray;');
        console.log('%c3. Refresh the page', 'color: gray;');
        console.log('%c', '');
        console.log('%cYour API key should match the API_KEY value in your .env file', 'color: red;');
    }
})();

// Helper function to set API key from console
window.setApiKey = function(key) {
    localStorage.setItem('apiKey', key);
    console.log('%c✓ API Key saved successfully!', 'color: green; font-size: 14px;');
    console.log('%cPlease refresh the page.', 'color: blue;');
};

console.log('%cQuick Setup: Run setApiKey("your-api-key") in console', 'color: #2196F3; font-size: 12px;');

