// popup.js

const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const settingsGrid = document.getElementById("settings-grid");
const noSettings = document.getElementById("no-settings");
const enableToggle = document.getElementById("enable-toggle");

function updateUI(settings, connected) {
  if (connected) {
    statusDot.classList.add("connected");
    statusText.textContent = "Connected to Vision Adaptive";
  } else {
    statusDot.classList.remove("connected");
    statusText.textContent = "App not running — open Vision Adaptive";
  }

  if (settings) {
    noSettings.style.display = "none";
    settingsGrid.style.display = "grid";
    document.getElementById("chip-brightness").textContent = (settings.brightness || "--") + "%";
    document.getElementById("chip-scale").textContent = settings.scale ? settings.scale.toFixed(1) + "x" : "--";
    document.getElementById("chip-contrast").textContent = settings.contrast ? settings.contrast.toFixed(1) + "x" : "--";
    document.getElementById("chip-spacing").textContent = (settings.spacing || 0) + "px";
  } else {
    noSettings.style.display = "block";
    settingsGrid.style.display = "none";
  }
}

// Load current state
chrome.storage.local.get(["visionSettings", "visionEnabled", "visionConnected"], (result) => {
  enableToggle.checked = result.visionEnabled !== false;
  updateUI(result.visionSettings, result.visionConnected !== false);
});

// Toggle enable/disable
enableToggle.addEventListener("change", () => {
  const enabled = enableToggle.checked;
  chrome.storage.local.set({ visionEnabled: enabled });

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, {
      type: enabled ? "VISION_ENABLE" : "VISION_DISABLE"
    });
  });
});

// Open dashboard
document.getElementById("open-app").addEventListener("click", () => {
  chrome.tabs.create({ url: "https://khiryhill.github.io/4Eyes/dashboard.html" });
});

// Refresh settings
document.getElementById("refresh-btn").addEventListener("click", () => {
  chrome.runtime.sendMessage({ type: "APPLY_NOW" }, () => {
    statusText.textContent = "Refreshing...";
    setTimeout(() => {
      chrome.storage.local.get(["visionSettings", "visionConnected"], (result) => {
        updateUI(result.visionSettings, result.visionConnected !== false);
      });
    }, 1000);
  });
});
