// content.js
// Applies vision comfort settings — reduces eye strain, does not correct vision

const STYLE_ID = "vision-adaptive-styles";

function applySettings(settings) {
  if (!settings) return;

  const {
    contrast = 1.0,
    spacing = 0,
    line_height = 1.6,
    font_weight = 400,
    brightness = 100
  } = settings;

  const existing = document.getElementById(STYLE_ID);
  if (existing) existing.remove();

  const style = document.createElement("style");
  style.id = STYLE_ID;
  style.textContent = `
    html {
      filter: contrast(${contrast}) brightness(${brightness / 100}) !important;
    }

    body, p, span, div, li, td, th,
    h1, h2, h3, h4, h5, h6,
    a, label, input, textarea, button, select {
      letter-spacing: ${spacing}px !important;
      line-height: ${line_height} !important;
      font-weight: ${font_weight} !important;
      word-spacing: ${spacing > 0 ? spacing * 2 : 0}px !important;
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
