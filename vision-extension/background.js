// background.js
// Polls the Vision Adaptive app every 2 seconds for updated settings
// and broadcasts them to all open tabs

const APP_URL = "http://localhost:5050/settings";
let currentSettings = null;

async function fetchSettings() {
  try {
    const response = await fetch(APP_URL);
    if (!response.ok) return;
    const settings = await response.json();

    // Only update if settings changed
    if (JSON.stringify(settings) !== JSON.stringify(currentSettings)) {
      currentSettings = settings;

      // Save to storage
      await chrome.storage.local.set({ visionSettings: settings });

      // Broadcast to all tabs
      const tabs = await chrome.tabs.query({});
      for (const tab of tabs) {
        try {
          await chrome.tabs.sendMessage(tab.id, {
            type: "VISION_SETTINGS_UPDATE",
            settings
          });
        } catch (e) {
          // Tab may not have content script, ignore
        }
      }
    }
  } catch (e) {
    // App not running, store disconnected state
    await chrome.storage.local.set({ visionConnected: false });
  }
}

// Poll every 2 seconds
setInterval(fetchSettings, 2000);
fetchSettings();

// Listen for popup requests
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "GET_SETTINGS") {
    sendResponse({ settings: currentSettings });
  }
  if (msg.type === "APPLY_NOW") {
    fetchSettings();
    sendResponse({ ok: true });
  }
  return true;
});