// background.js
const API_URL = 'https://4eyes-production.up.railway.app';

async function fetchSettings() {
  try {
    const token = await getToken();
    if (!token) {
      await chrome.storage.local.set({ visionConnected: false });
      return;
    }

    const response = await fetch(API_URL + '/extension/settings', {
      headers: { 'Authorization': 'Bearer ' + token }
    });

    if (!response.ok) {
      await chrome.storage.local.set({ visionConnected: false });
      return;
    }

    const data = await response.json();
    const settings = data.settings;

    await chrome.storage.local.set({ visionSettings: settings, visionConnected: true });

    broadcastToTabs({ type: 'VISION_SETTINGS_UPDATE', settings });

  } catch (e) {
    await chrome.storage.local.set({ visionConnected: false });
  }
}

async function broadcastToTabs(message) {
  const tabs = await chrome.tabs.query({});
  for (const tab of tabs) {
    try { await chrome.tabs.sendMessage(tab.id, message); } catch (e) {}
  }
}

async function getToken() {
  return new Promise(resolve => {
    chrome.storage.local.get('4eyes_token', result => {
      console.log('Token found:', result['4eyes_token'] ? 'YES' : 'NO');
      resolve(result['4eyes_token'] || null);
    });
  });
}

// Poll every 5 seconds
setInterval(fetchSettings, 5000);
fetchSettings();

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'GET_SETTINGS') {
    chrome.storage.local.get(['visionSettings', 'visionConnected'], result => {
      sendResponse(result);
    });
    return true;
  }
  if (msg.type === 'SET_TOKEN') {
    chrome.storage.local.set({ '4eyes_token': msg.token }, () => {
      fetchSettings();
      sendResponse({ ok: true });
    });
    return true;
  }
  if (msg.type === 'LOGOUT') {
    chrome.storage.local.remove(['4eyes_token', 'visionSettings', 'visionConnected', 'visionFont', 'visionLensCoating'], () => {
      sendResponse({ ok: true });
    });
    return true;
  }
  if (msg.type === 'APPLY_NOW') {
    fetchSettings();
    sendResponse({ ok: true });
    return true;
  }
  if (msg.type === 'VISION_FONT_UPDATE') {
    console.log('Font update received:', msg.fontFamily);
    chrome.storage.local.set({ visionFont: msg.fontFamily });
    broadcastToTabs({ type: 'VISION_FONT_UPDATE', fontFamily: msg.fontFamily });
    sendResponse({ ok: true });
    return true;
  }
  if (msg.type === 'VISION_LENS_UPDATE') {
    console.log('Lens coating update received:', msg.coating);
    chrome.storage.local.set({ visionLensCoating: msg.coating });
    broadcastToTabs({ type: 'VISION_LENS_UPDATE', coating: msg.coating });
    sendResponse({ ok: true });
    return true;
  }
});