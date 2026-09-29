import re

with open('backend/templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Include safetyColors.js in head
if 'safetyColors.js' not in html:
    html = html.replace('</head>', '<script src="/static/js/safetyColors.js"></script>\n</head>')

# 2. Update Map Legend HTML to 5-tier + No Data
legend_html = '''
  <div id="safety-map-legend" style="display:none; position:fixed; bottom:28px; left:20px; z-index:1500; background:rgba(10,18,36,0.96); backdrop-filter:blur(14px); border:1.5px solid #334155; border-radius:14px; padding:12px 16px; min-width:210px; box-shadow:0 8px 32px rgba(0,0,0,0.6);">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
      <span style="font-size:11px; font-weight:800; color:#A78BFA; letter-spacing:0.8px;">🛡️ SAFETY MAP LEGEND</span>
      <button onclick="document.getElementById('safety-map-legend').style.display='none'" style="background:none;border:none;color:#94A3B8;cursor:pointer;font-size:12px;">✕</button>
    </div>
    <div id="legend-swatches" style="display:flex; flex-direction:column; gap:5px; font-size:11.5px; color:#CBD5E1;">
      <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#1B9E4B;margin-right:7px;vertical-align:middle;"></span>🟢 80–100 Very Safe</span>
      <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#7ACB5A;margin-right:7px;vertical-align:middle;"></span>🟢 60–79 Safe</span>
      <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#F5D33F;margin-right:7px;vertical-align:middle;"></span>🟡 40–59 Moderate</span>
      <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#F28C28;margin-right:7px;vertical-align:middle;"></span>🟠 20–39 Risky</span>
      <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#D62828;margin-right:7px;vertical-align:middle;"></span>🔴 0–19 Unsafe</span>
      <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#9AA0A6;margin-right:7px;vertical-align:middle;"></span>⚪ No data (Dashed)</span>
    </div>
    <div style="margin-top:8px; display:flex; align-items:center; justify-content:space-between; font-size:10px; color:#94A3B8; border-top:1px solid #1E293B; padding-top:6px;">
      <span>Colorblind Mode</span>
      <input type="checkbox" id="colorblind-toggle" onchange="toggleColorblindMode(this.checked)" style="cursor:pointer;">
    </div>
  </div>
'''

html = re.sub(r'<div id="safety-map-legend"[\s\S]*?</div>\s*</div>', legend_html, html)

# 3. Add Day/Night toggle & Colorblind toggle support in HTML floating-map-controls
controls_html = '''
      <button class="nav-tab-btn map-style-btn" data-style="light" onclick="setMapStyle('light')" style="padding: 6px 10px; font-size: 11px;">☀️ Light</button>
      <button class="nav-tab-btn map-style-btn active" data-style="dark" onclick="setMapStyle('dark')" style="padding: 6px 10px; font-size: 11px;">🌙 Dark</button>
      <button class="nav-tab-btn map-style-btn" data-style="satellite" onclick="setMapStyle('satellite')" style="padding: 6px 10px; font-size: 11px;">🛰️ Satellite</button>
      <button class="nav-tab-btn map-style-btn" data-style="streets" onclick="setMapStyle('streets')" style="padding: 6px 10px; font-size: 11px;">🗺️ Streets</button>
      <button class="nav-tab-btn" onclick="openVpsVisualViewModal()" style="padding: 6px 12px; font-size: 11px; color: var(--primary-light); background: rgba(59, 130, 246, 0.2); border: 1px solid var(--primary-light); border-radius: 8px;">📷 Visual View (360°)</button>
      <button id="safety-map-mode-btn" class="nav-tab-btn" onclick="safetyMap_toggle()" style="padding: 6px 12px; font-size: 11px; color: #A78BFA; background: rgba(167,139,250,0.15); border: 1px solid #A78BFA; border-radius: 8px;">🛡️ Safety Map</button>
      <div class="nav-tab-btn" style="padding: 4px 8px; font-size: 11px; background: rgba(30,41,59,0.9); border: 1px solid #334155; border-radius: 8px; display: flex; align-items: center; gap: 6px;">
        <button id="sm-day-btn" onclick="safetyMap_setTime('day')" style="background:transparent;border:none;color:#FACC15;cursor:pointer;padding:2px 4px;font-size:12px;">☀️ Day</button>
        <div style="width:1px;height:12px;background:#334155;"></div>
        <button id="sm-night-btn" onclick="safetyMap_setTime('night')" style="background:transparent;border:none;color:var(--text-muted);cursor:pointer;padding:2px 4px;font-size:12px;">🌙 Night</button>
      </div>
'''
html = re.sub(r'<div class="floating-map-controls">[\s\S]*?</div>\s*</div>', '<div class="floating-map-controls">\n' + controls_html + '\n    </div>', html)

with open('backend/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated HTML layout.")
