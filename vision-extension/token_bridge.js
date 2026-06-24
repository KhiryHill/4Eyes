// token_bridge.js
// Bridges localStorage and extension messaging

function syncToken() {
  const token = localStorage.getItem('4eyes_token');
  if (token) {
    chrome.runtime.sendMessage({ type: 'SET_TOKEN', token });
  }
}

function syncFont() {
  const font = localStorage.getItem('4eyes_font') || '';
  chrome.runtime.sendMessage({
    type: 'VISION_FONT_UPDATE',
    fontFamily: font
  });
}

function syncLensCoating() {
  const coating = localStorage.getItem('4eyes_lens_coating') || 'none';
  chrome.runtime.sendMessage({
    type: 'VISION_LENS_UPDATE',
    coating: coating
  });
}

// Sync on page load
syncToken();
syncFont();
syncLensCoating();

// Watch localStorage for changes
window.addEventListener('storage', (e) => {
  if (e.key === '4eyes_token') syncToken();
  if (e.key === '4eyes_font') syncFont();
  if (e.key === '4eyes_lens_coating') syncLensCoating();
});

// Poll every second
setInterval(syncFont, 1000);
setInterval(syncLensCoating, 1000);