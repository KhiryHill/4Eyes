// content.js
// Applies vision comfort settings — reduces eye strain, does not correct vision

const STYLE_ID = "vision-adaptive-styles";
const FONT_LINK_ID = "vision-adaptive-font";

function applySettings(settings) {
  if (!settings) return;

  const {
    contrast = 1.0,
    spacing = 0,
    line_height = 1.6,
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
      word-spacing: ${spacing > 0 ? spacing * 2 : 0}px !important;
    }
  `;
  document.head.appendChild(style);
}

function applyFont(fontFamily) {
  // Remove existing font override style
  const existingStyle = document.getElementById(FONT_LINK_ID + '-style');
  if (existingStyle) existingStyle.remove();

  if (!fontFamily) return;

  const style = document.createElement("style");
  style.id = FONT_LINK_ID + '-style';
  style.textContent = `
    body, p, span, div, li, td, th,
    h1, h2, h3, h4, h5, h6,
    a, label, input, textarea, button, select {
      font-family: ${fontFamily} !important;
    }
  `;
  document.head.appendChild(style);
}

function removeSettings() {
  const existing = document.getElementById(STYLE_ID);
  if (existing) existing.remove();
  const existingFont = document.getElementById(FONT_LINK_ID + '-style');
  if (existingFont) existingFont.remove();
}

// Load saved settings on page load
chrome.storage.local.get(["visionSettings", "visionEnabled", "visionFont"], (result) => {
  if (result.visionEnabled !== false && result.visionSettings) {
    applySettings(result.visionSettings);
  }
  if (result.visionFont) {
    applyFont(result.visionFont);
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
  if (msg.type === "VISION_FONT_UPDATE") {
    applyFont(msg.fontFamily);
    chrome.storage.local.set({ visionFont: msg.fontFamily });
  }
  if (msg.type === "VISION_DISABLE") {
    removeSettings();
  }
  if (msg.type === "VISION_ENABLE") {
    chrome.storage.local.get(["visionSettings", "visionFont"], (result) => {
      if (result.visionSettings) applySettings(result.visionSettings);
      if (result.visionFont) applyFont(result.visionFont);
    });
  }
});
