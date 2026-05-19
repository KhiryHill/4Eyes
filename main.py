import sys
import os
import platform
import subprocess
import webbrowser
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# -------------------------
# Detect Platform
# -------------------------
OS = platform.system()

# -------------------------
# Get Monitors
# -------------------------
try:
    from screeninfo import get_monitors
    monitors = get_monitors()
    monitor_names = [f"Monitor {i+1}" for i in range(len(monitors))]
except Exception:
    monitor_names = ["Monitor 1"]

# -------------------------
# Current Settings (shared state for extension)
# -------------------------
current_settings = {
    "brightness": 60,
    "scale": 1.0,
    "contrast": 1.0,
    "spacing": 0,
    "lineHeight": 1.6
}

# -------------------------
# Brightness Control
# -------------------------
def set_brightness_all(value):
    try:
        if OS == "Darwin":
            level = round(value / 100, 2)
            subprocess.run([
                "osascript", "-e",
                f'tell application "System Events" to set brightness of every display to {level}'
            ])
        elif OS == "Windows":
            import screen_brightness_control as sbc
            sbc.set_brightness(value)
        elif OS == "Linux":
            subprocess.run(["xrandr", "--output", "eDP-1", "--brightness", str(round(value / 100, 2))])
        return True
    except Exception as e:
        print("Brightness error:", e)
        return False

def set_brightness_selected(value, index):
    try:
        if OS == "Darwin":
            level = round(value / 100, 2)
            subprocess.run([
                "osascript", "-e",
                f'tell application "System Events" to set brightness of display {index + 1} to {level}'
            ])
        elif OS == "Windows":
            import screen_brightness_control as sbc
            sbc.set_brightness(value, display=index)
        elif OS == "Linux":
            result = subprocess.run(["xrandr", "--listmonitors"], capture_output=True, text=True)
            lines = [l.strip() for l in result.stdout.strip().split("\n")[1:]]
            if index < len(lines):
                display_name = lines[index].split()[-1]
                subprocess.run(["xrandr", "--output", display_name, "--brightness", str(round(value / 100, 2))])
        return True
    except Exception as e:
        print("Monitor brightness error:", e)
        return False

# -------------------------
# System Tray
# -------------------------
def create_tray_icon(url):
    try:
        from PIL import Image, ImageDraw
        import pystray

        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([8, 20, 56, 44], fill=(91, 141, 238))
        draw.ellipse([24, 26, 40, 38], fill=(13, 15, 20))
        draw.ellipse([27, 29, 34, 35], fill=(255, 255, 255))

        def open_dashboard(icon, item):
            webbrowser.open(url)

        def quit_app(icon, item):
            icon.stop()
            os._exit(0)

        menu = pystray.Menu(
            pystray.MenuItem("Open Dashboard", open_dashboard, default=True),
            pystray.MenuItem("Quit Vision Adaptive", quit_app)
        )

        icon = pystray.Icon("VisionAdaptive", img, "Vision Adaptive Display Pro", menu)
        icon.run()

    except Exception as e:
        print("System tray error:", e)
        print("Running without system tray.")

# -------------------------
# HTML UI
# -------------------------
MONITOR_OPTIONS = "\n".join(
    f'<option value="{i}">{name}</option>'
    for i, name in enumerate(monitor_names)
)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Vision Adaptive Display Pro</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet"/>
<style>
  :root {
    --bg: #0d0f14;
    --surface: #161a23;
    --border: #252a38;
    --accent: #5b8dee;
    --accent2: #a78bfa;
    --text: #e8eaf0;
    --muted: #6b7280;
    --success: #34d399;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 40px 20px;
    background-image: radial-gradient(ellipse at 20% 20%, rgba(91,141,238,0.08) 0%, transparent 60%),
                      radial-gradient(ellipse at 80% 80%, rgba(167,139,250,0.06) 0%, transparent 60%);
  }

  h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
  }

  .subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 8px; font-weight: 300; }

  .badges {
    display: flex;
    gap: 8px;
    margin-bottom: 28px;
    flex-wrap: wrap;
    justify-content: center;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .badge-live {
    background: rgba(52,211,153,0.1);
    border: 1px solid rgba(52,211,153,0.3);
    color: #34d399;
  }

  .badge-platform {
    background: rgba(91,141,238,0.1);
    border: 1px solid rgba(91,141,238,0.3);
    color: var(--accent);
  }

  .badge-extension {
    background: rgba(167,139,250,0.1);
    border: 1px solid rgba(167,139,250,0.3);
    color: var(--accent2);
  }

  .live-dot {
    width: 6px;
    height: 6px;
    background: #34d399;
    border-radius: 50%;
    animation: pulse 1.5s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    width: 100%;
    max-width: 520px;
    margin-bottom: 16px;
  }

  .card-title {
    font-size: 0.7rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--muted);
    margin-bottom: 18px;
  }

  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }

  .eye-section {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 12px;
    transition: border-color 0.3s;
  }

  .eye-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--accent);
    margin-bottom: 10px;
  }

  label {
    display: block;
    font-size: 0.78rem;
    color: var(--muted);
    margin-bottom: 6px;
    font-weight: 500;
  }

  input[type="number"] {
    width: 100%;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 12px;
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
  }

  input[type="number"]:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(91,141,238,0.1);
  }

  input[type="number"].updated {
    border-color: #34d399;
    box-shadow: 0 0 0 3px rgba(52,211,153,0.1);
  }

  .slider-row { margin-bottom: 20px; }

  .slider-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .slider-value { font-size: 0.85rem; color: var(--accent); font-weight: 500; }

  input[type="range"] {
    width: 100%;
    -webkit-appearance: none;
    height: 4px;
    border-radius: 2px;
    background: var(--border);
    outline: none;
  }

  input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    cursor: pointer;
    box-shadow: 0 0 10px rgba(91,141,238,0.4);
  }

  .radio-group { display: flex; gap: 10px; margin-bottom: 14px; }

  .radio-btn {
    flex: 1;
    padding: 10px;
    border: 1px solid var(--border);
    border-radius: 8px;
    text-align: center;
    cursor: pointer;
    font-size: 0.82rem;
    color: var(--muted);
    transition: all 0.2s;
    user-select: none;
  }

  .radio-btn.active {
    border-color: var(--accent);
    color: var(--accent);
    background: rgba(91,141,238,0.08);
  }

  select {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 12px;
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    outline: none;
    margin-top: 10px;
  }

  .preview-box {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    transition: all 0.4s ease;
  }

  .preview-text {
    font-size: 15px;
    line-height: 1.6;
    transition: all 0.4s ease;
  }

  .axis-indicator {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px;
    margin-top: 12px;
    font-size: 0.8rem;
    color: var(--muted);
    display: none;
  }

  .axis-indicator.visible { display: block; }
  .axis-indicator strong { color: var(--accent2); }

  .settings-summary {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-top: 12px;
  }

  .setting-chip {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px;
    text-align: center;
  }

  .setting-chip-label { font-size: 0.65rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }
  .setting-chip-value { font-size: 0.95rem; color: var(--accent); font-weight: 600; margin-top: 2px; }

  .extension-banner {
    background: rgba(167,139,250,0.06);
    border: 1px solid rgba(167,139,250,0.2);
    border-radius: 10px;
    padding: 12px 14px;
    font-size: 0.8rem;
    color: var(--muted);
    margin-bottom: 10px;
    text-align: center;
  }

  .extension-banner strong { color: var(--accent2); }
</style>
</head>
<body>

<h1>Vision Adaptive Display Pro</h1>
<p class="subtitle">Personalized display settings for your vision needs</p>

<div class="badges">
  <div class="badge badge-live"><div class="live-dot"></div>Live Adjustment</div>
  <div class="badge badge-platform">PLATFORM_NAME</div>
  <div class="badge badge-extension">Chrome Extension Active</div>
</div>

<div class="extension-banner">
  <strong>Chrome Extension:</strong> Your prescription settings sync automatically to every website you visit.
</div>

<div class="card">
  <div class="card-title">Prescription Input — adjusts display as you type</div>

  <div class="eye-section">
    <div class="eye-label">Right Eye (OD)</div>
    <div class="grid-3">
      <div>
        <label>SPH</label>
        <input type="number" id="right_sph" step="0.25" placeholder="-2.00" oninput="onPrescriptionChange(this)"/>
      </div>
      <div>
        <label>CYL</label>
        <input type="number" id="right_cyl" step="0.25" placeholder="-0.50" oninput="onPrescriptionChange(this)"/>
      </div>
      <div>
        <label>Axis (1-180)</label>
        <input type="number" id="right_axis" min="1" max="180" step="1" placeholder="90" oninput="onPrescriptionChange(this)"/>
      </div>
    </div>
  </div>

  <div class="eye-section">
    <div class="eye-label">Left Eye (OS)</div>
    <div class="grid-3">
      <div>
        <label>SPH</label>
        <input type="number" id="left_sph" step="0.25" placeholder="-1.75" oninput="onPrescriptionChange(this)"/>
      </div>
      <div>
        <label>CYL</label>
        <input type="number" id="left_cyl" step="0.25" placeholder="-0.50" oninput="onPrescriptionChange(this)"/>
      </div>
      <div>
        <label>Axis (1-180)</label>
        <input type="number" id="left_axis" min="1" max="180" step="1" placeholder="85" oninput="onPrescriptionChange(this)"/>
      </div>
    </div>
  </div>

  <div class="grid-2" style="margin-bottom:14px">
    <div>
      <label>ADD (Reading)</label>
      <input type="number" id="add_val" step="0.25" placeholder="1.00" oninput="onPrescriptionChange(this)"/>
    </div>
  </div>

  <div class="axis-indicator" id="axis-indicator">
    <strong>Axis Insight:</strong> <span id="axis-insight-text"></span>
  </div>

  <div class="settings-summary" id="settings-summary" style="display:none">
    <div class="setting-chip">
      <div class="setting-chip-label">Brightness</div>
      <div class="setting-chip-value" id="chip-brightness">--</div>
    </div>
    <div class="setting-chip">
      <div class="setting-chip-label">Text Scale</div>
      <div class="setting-chip-value" id="chip-scale">--</div>
    </div>
    <div class="setting-chip">
      <div class="setting-chip-label">Contrast</div>
      <div class="setting-chip-value" id="chip-contrast">--</div>
    </div>
    <div class="setting-chip">
      <div class="setting-chip-label">Spacing</div>
      <div class="setting-chip-value" id="chip-spacing">--</div>
    </div>
    <div class="setting-chip">
      <div class="setting-chip-label">Line Height</div>
      <div class="setting-chip-value" id="chip-lineheight">--</div>
    </div>
  </div>
</div>

<div class="card">
  <div class="card-title">Monitor Mode</div>
  <div class="radio-group">
    <div class="radio-btn active" id="mode-all" onclick="setMode('All')">All Monitors</div>
    <div class="radio-btn" id="mode-single" onclick="setMode('Single')">Single Monitor</div>
  </div>
  <label>Select Monitor</label>
  <select id="monitor_select">
    MONITOR_OPTIONS
  </select>
</div>

<div class="card">
  <div class="card-title">Manual Overrides</div>

  <div class="slider-row">
    <div class="slider-header">
      <label style="margin:0">Brightness</label>
      <span class="slider-value" id="brightness-val">60%</span>
    </div>
    <input type="range" id="brightness" min="20" max="100" value="60" oninput="updateSlider('brightness', this.value, '%'); applyBrightness()"/>
  </div>

  <div class="slider-row">
    <div class="slider-header">
      <label style="margin:0">Text Scale</label>
      <span class="slider-value" id="scale-val">1.5x</span>
    </div>
    <input type="range" id="scale" min="10" max="30" value="15" oninput="updateSlider('scale', (this.value/10).toFixed(1), 'x'); updatePreview()"/>
  </div>

  <div class="slider-row">
    <div class="slider-header">
      <label style="margin:0">Contrast</label>
      <span class="slider-value" id="contrast-val">1.2x</span>
    </div>
    <input type="range" id="contrast" min="10" max="30" value="12" oninput="updateSlider('contrast', (this.value/10).toFixed(1), 'x'); updatePreview()"/>
  </div>

  <div class="slider-row">
    <div class="slider-header">
      <label style="margin:0">Letter Spacing</label>
      <span class="slider-value" id="spacing-val">0px</span>
    </div>
    <input type="range" id="spacing" min="0" max="10" value="0" oninput="updateSlider('spacing', this.value, 'px'); updatePreview()"/>
  </div>

  <div class="slider-row">
    <div class="slider-header">
      <label style="margin:0">Line Height</label>
      <span class="slider-value" id="lineheight-val">1.6</span>
    </div>
    <input type="range" id="lineheight" min="10" max="30" value="16" oninput="updateSlider('lineheight', (this.value/10).toFixed(1), ''); updatePreview()"/>
  </div>
</div>

<div class="card">
  <div class="card-title">Readability Preview</div>
  <div class="preview-box" id="preview-box">
    <p class="preview-text" id="preview-text">This is a readability preview.<br/>Adjusting for your vision needs.<br/>The quick brown fox jumps over the lazy dog.</p>
  </div>
</div>

<script>
  let currentMode = 'All';
  let debounceTimer = null;

  function setMode(mode) {
    currentMode = mode;
    document.getElementById('mode-all').classList.toggle('active', mode === 'All');
    document.getElementById('mode-single').classList.toggle('active', mode === 'Single');
  }

  function updateSlider(id, value, unit) {
    document.getElementById(id + '-val').textContent = value + unit;
  }

  function updatePreview() {
    const scale = parseFloat(document.getElementById('scale').value) / 10;
    const contrast = parseFloat(document.getElementById('contrast').value) / 10;
    const spacing = parseFloat(document.getElementById('spacing').value);
    const lineHeight = parseFloat(document.getElementById('lineheight').value) / 10;
    const preview = document.getElementById('preview-text');
    const box = document.getElementById('preview-box');
    preview.style.fontSize = Math.round(10 * scale) + 'px';
    preview.style.letterSpacing = spacing + 'px';
    preview.style.lineHeight = lineHeight;
    box.style.filter = 'contrast(' + contrast + ')';
  }

  function applyBrightness() {
    const brightness = document.getElementById('brightness').value;
    const monitorIndex = document.getElementById('monitor_select').selectedIndex;
    fetch('/set_brightness?value=' + brightness + '&mode=' + currentMode + '&index=' + monitorIndex)
      .then(r => r.json()).catch(() => {});
    updatePreview();
  }

  function syncSettingsToExtension(settings) {
    fetch('/update_settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    }).catch(() => {});
  }

  function flashInput(el) {
    el.classList.add('updated');
    setTimeout(() => el.classList.remove('updated'), 800);
  }

  function getAxisInsight(rAxis, lAxis, rCyl, lCyl) {
    const avgAxis = (rAxis + lAxis) / 2;
    if (Math.abs(rCyl) === 0 && Math.abs(lCyl) === 0) return null;
    if (avgAxis >= 160 || avgAxis <= 20) {
      return 'Horizontal astigmatism detected. Line height and letter spacing increased for better readability.';
    } else if (avgAxis >= 70 && avgAxis <= 110) {
      return 'Vertical astigmatism detected. Font size and contrast increased to sharpen vertical text.';
    } else {
      return 'Oblique astigmatism detected. Contrast and spacing increased for visual comfort.';
    }
  }

  function onPrescriptionChange(el) {
    flashInput(el);
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => applyPrescription(), 400);
  }

  function applyPrescription() {
    const rSph = parseFloat(document.getElementById('right_sph').value) || 0;
    const lSph = parseFloat(document.getElementById('left_sph').value) || 0;
    const rCyl = parseFloat(document.getElementById('right_cyl').value) || 0;
    const lCyl = parseFloat(document.getElementById('left_cyl').value) || 0;
    const rAxis = parseFloat(document.getElementById('right_axis').value) || 90;
    const lAxis = parseFloat(document.getElementById('left_axis').value) || 90;
    const addVal = parseFloat(document.getElementById('add_val').value) || 0;

    if (rSph === 0 && lSph === 0 && rCyl === 0 && lCyl === 0) return;

    const avgSph = (Math.abs(rSph) + Math.abs(lSph)) / 2;
    const avgCyl = (Math.abs(rCyl) + Math.abs(lCyl)) / 2;
    const avgAxis = (rAxis + lAxis) / 2;

    let scale = Math.min(3, 1 + avgSph * 0.3);
    let contrast = Math.min(3, 1 + avgCyl * 0.5);
    let brightness = Math.max(20, Math.min(100, Math.round(100 - avgSph * 20)));
    let spacing = 0;
    let lineHeight = 16;

    if (avgCyl > 0) {
      if (avgAxis >= 160 || avgAxis <= 20) {
        lineHeight = Math.min(30, 16 + Math.round(avgCyl * 4));
        spacing = Math.min(10, Math.round(avgCyl * 2));
      } else if (avgAxis >= 70 && avgAxis <= 110) {
        scale = Math.min(3, scale + avgCyl * 0.2);
        contrast = Math.min(3, contrast + avgCyl * 0.2);
      } else {
        contrast = Math.min(3, contrast + avgCyl * 0.15);
        spacing = Math.min(10, Math.round(avgCyl));
      }
    }

    if (addVal > 0) {
      scale = Math.min(3, scale + addVal * 0.1);
      lineHeight = Math.min(30, lineHeight + Math.round(addVal * 2));
    }

    document.getElementById('brightness').value = brightness;
    document.getElementById('scale').value = Math.round(scale * 10);
    document.getElementById('contrast').value = Math.round(contrast * 10);
    document.getElementById('spacing').value = spacing;
    document.getElementById('lineheight').value = lineHeight;

    updateSlider('brightness', brightness, '%');
    updateSlider('scale', scale.toFixed(1), 'x');
    updateSlider('contrast', contrast.toFixed(1), 'x');
    updateSlider('spacing', spacing, 'px');
    updateSlider('lineheight', (lineHeight / 10).toFixed(1), '');

    updatePreview();

    const monitorIndex = document.getElementById('monitor_select').selectedIndex;
    fetch('/set_brightness?value=' + brightness + '&mode=' + currentMode + '&index=' + monitorIndex)
      .then(r => r.json()).catch(() => {});

    // Sync to extension
    syncSettingsToExtension({
      brightness,
      scale: parseFloat(scale.toFixed(2)),
      contrast: parseFloat(contrast.toFixed(2)),
      spacing,
      lineHeight: parseFloat((lineHeight / 10).toFixed(2))
    });

    const insight = getAxisInsight(rAxis, lAxis, rCyl, lCyl);
    const indicator = document.getElementById('axis-indicator');
    if (insight) {
      document.getElementById('axis-insight-text').textContent = insight;
      indicator.classList.add('visible');
    } else {
      indicator.classList.remove('visible');
    }

    const summary = document.getElementById('settings-summary');
    summary.style.display = 'grid';
    document.getElementById('chip-brightness').textContent = brightness + '%';
    document.getElementById('chip-scale').textContent = scale.toFixed(1) + 'x';
    document.getElementById('chip-contrast').textContent = contrast.toFixed(1) + 'x';
    document.getElementById('chip-spacing').textContent = spacing + 'px';
    document.getElementById('chip-lineheight').textContent = (lineHeight / 10).toFixed(1);
  }

  updatePreview();
</script>

</body>
</html>"""

HTML = HTML.replace("MONITOR_OPTIONS", MONITOR_OPTIONS)
HTML = HTML.replace("PLATFORM_NAME", OS)

# -------------------------
# HTTP Server
# -------------------------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(HTML.encode())

        elif parsed.path == "/settings":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(current_settings).encode())

        elif parsed.path == "/set_brightness":
            params = parse_qs(parsed.query)
            value = int(params.get("value", [60])[0])
            mode = params.get("mode", ["All"])[0]
            index = int(params.get("index", [0])[0])

            current_settings["brightness"] = value

            if mode == "All":
                success = set_brightness_all(value)
            else:
                success = set_brightness_selected(value, index)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": success}).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/update_settings":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                current_settings.update(data)
            except Exception:
                pass

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())

        else:
            self.send_response(404)
            self.end_headers()

# -------------------------
# Launch Server
# -------------------------
PORT = 5050
server = HTTPServer(("localhost", PORT), Handler)
url = f"http://localhost:{PORT}"

print(f"Vision Adaptive Display Pro running at {url}")
print(f"Platform: {OS}")
print("Running in system tray. Press Ctrl+C to stop.\n")

server_thread = threading.Thread(target=server.serve_forever, daemon=True)
server_thread.start()

threading.Timer(1, lambda: webbrowser.open(url)).start()

create_tray_icon(url)