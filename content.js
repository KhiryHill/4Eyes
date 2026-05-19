// content.js
// Runs on every webpage and applies vision prescription settings

const STYLE_ID = "vision-adaptive-styles";

function applySettings(settings) {
  if (!settings) return;

  const {
    scale = 1.0,
    contrast = 1.0,
    spacing = 0,
    lineHeight = 1.6
  } = settings;

  // Remove existing style if present
  const existing = document.getElementById(STYLE_ID);
  if (existing) existing.remove();

  // Create new style block
  const style = document.createElement("style");
  style.id = STYLE_ID;
  style.textContent = `
    body, p, span, div, li, td, th, h1, h2, h3, h4, h5, h6,
    a, label, input, textarea, button, select {
      font-size: ${scale > 1 ? scale + "em" : ""} !important;
      letter-spacing: ${spacing}px !important;
      line-height: ${lineHeight} !important;
    }

    html {
      filter: contrast(${contrast}) !important;
    }
  `;

  document.head.appendChild(style);
}

function removeSettings() {
  const existing = document.getElementById(STYLE_ID);
  if (existing) existing.remove();
}

// Load saved settings on page load
chrome.storage.local.get(["visionSettings", "visionEnabled"], (result) => {
  if (result.visionEnabled !== false && result.visionSettings) {
    applySettings(result.visionSettings);
  }
});

// Listen for live updates from background
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === "VISION_SETTINGS_UPDATE") {
    chrome.storage.local.get("visionEnabled", (result) => {
      if (result.visionEnabled !== false) {
        applySettings(msg.settings);
      }
    });
  }
  if (msg.type === "VISION_DISABLE") {
    removeSettings();
  }
  if (msg.type === "VISION_ENABLE") {
    chrome.storage.local.get("visionSettings", (result) => {
      if (result.visionSettings) applySettings(result.visionSettings);
    });
  }
});