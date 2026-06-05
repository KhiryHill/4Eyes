// token_bridge.js
// Bridges localStorage and extension messaging

function syncToken() {
  const token = localStorage.getItem('4eyes_token');
  if (token) {
    chrome.runtime.sendMessage({ type: 'SET_TOKEN', token });
  }
}

function syncFont() {
  const font = localStorage.getItem('4eyes_font');
  chrome.runtime.sendMessage({ 
    type: 'VISION_FONT_UPDATE', 
    fontFamily: font || '' 
  });
}

// Sync on page load
syncToken();
syncFont();

// Watch localStorage for changes
window.addEventListener('storage', (e) => {
  if (e.key === '4eyes_token') syncToken();
  if (e.key === '4eyes_font') syncFont();
});

// Also poll every second for font changes
setInterval(syncFont, 1000);