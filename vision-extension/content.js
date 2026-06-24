// content.js
const STYLE_ID = "vision-adaptive-styles";
const FONT_LINK_ID = "vision-adaptive-font";
const LENS_STYLE_ID = "vision-adaptive-lens";

function applySettings(settings) {
  if (!settings) return;

  const {
    contrast = 1.0,
    spacing = 0,
    line_height = 1.6,
    brightness = 100,
    font_weight = 400
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
      font-weight: ${font_weight} !important;
    }
  `;
  document.head.appendChild(style);
}

function applyLensCoating(coating) {
  const existing = document.getElementById(LENS_STYLE_ID);
  if (existing) existing.remove();
  if (!coating || coating === 'none') return;

  let filter = '';
  if (coating === 'blue_light') {
    filter = 'hue-rotate(-10deg) saturate(110%) brightness(1.03)';
  } else if (coating === 'uv') {
    filter = 'brightness(1.02) saturate(105%) contrast(1.02)';
  } else if (coating === 'photochromic') {
    const hour = new Date().getHours();
    const isDaytime = hour >= 7 && hour <= 19;
    filter = isDaytime ? 'brightness(0.92) saturate(95%)' : 'brightness(0.98)';
  }

  if (!filter) return;

  const style = document.createElement("style");
  style.id = LENS_STYLE_ID;
  style.textContent = `
    html {
      filter: ${filter} !important;
    }
  `;
  document.head.appendChild(style);
}

function applyFont(fontFamily) {
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
  [STYLE_ID, LENS_STYLE_ID, FONT_LINK_ID + '-style'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.remove();
  });
}

chrome.storage.local.get(["visionSettings", "visionEnabled", "visionFont", "visionLensCoating"], (result) => {
  if (result.visionEnabled !== false && result.visionSettings) {
    applySettings(result.visionSettings);
  }
  if (result.visionLensCoating) {
    applyLensCoating(result.visionLensCoating);
  }
  if (result.visionFont) {
    applyFont(result.visionFont);
  }
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === "VISION_SETTINGS_UPDATE") {
    chrome.storage.local.get("visionEnabled", (result) => {
      if (result.visionEnabled !== false) applySettings(msg.settings);
    });
  }
  if (msg.type === "VISION_FONT_UPDATE") {
    applyFont(msg.fontFamily);
    chrome.storage.local.set({ visionFont: msg.fontFamily });
  }
  if (msg.type === "VISION_LENS_UPDATE") {
    applyLensCoating(msg.coating);
    chrome.storage.local.set({ visionLensCoating: msg.coating });
  }
  if (msg.type === "VISION_DISABLE") removeSettings();
  if (msg.type === "VISION_ENABLE") {
    chrome.storage.local.get(["visionSettings", "visionFont", "visionLensCoating"], (result) => {
      if (result.visionSettings) applySettings(result.visionSettings);
      if (result.visionLensCoating) applyLensCoating(result.visionLensCoating);
      if (result.visionFont) applyFont(result.visionFont);
    });
  }
});