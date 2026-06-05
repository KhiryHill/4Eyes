// token_bridge.js
// Reads token from dashboard localStorage and sends to extension

function syncToken() {
  const token = localStorage.getItem('4eyes_token');
  if (token) {
    chrome.runtime.sendMessage({ type: 'SET_TOKEN', token });
  }
}

// Sync on page load
syncToken();

// Sync every 2 seconds in case user just logged in
setInterval(syncToken, 2000);