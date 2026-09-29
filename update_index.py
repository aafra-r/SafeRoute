import re

with open('backend/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Turn on Safety Map mode by default (adding setTimeout in initMap)
if 'setTimeout(() => safetyMap_activate(), 1500);' not in content:
    content = re.sub(
        r'(function initMap\(\) \{[\s\S]*?syncUserProfileUI\(\);)', 
        r'\1\n      setTimeout(() => safetyMap_activate(), 1500);', 
        content
    )

# 2. Add Day/Night toggle UI
toggle_html = '''<div class="nav-tab-btn" style="padding: 6px; font-size: 11px; background: rgba(30,41,59,0.9); border: 1px solid #334155; border-radius: 8px; display: flex; align-items: center; gap: 4px;">
        <button id="sm-day-btn" onclick="safetyMap_setTime('day')" style="background:transparent;border:none;color:var(--text-muted);cursor:pointer;padding:2px 4px;">☀️</button>
        <div style="width:1px;height:12px;background:#334155;"></div>
        <button id="sm-night-btn" onclick="safetyMap_setTime('night')" style="background:transparent;border:none;color:var(--text-muted);cursor:pointer;padding:2px 4px;">🌙</button>
      </div>'''

if 'sm-day-btn' not in content:
    content = re.sub(
        r'(<button id="safety-map-mode-btn".*?</button>)',
        r'\1\n      ' + toggle_html,
        content
    )

# 3. Add JS variables and logic for Day/Night toggle & URL append
if 'var safetyMap_timeOfDay =' not in content:
    content = re.sub(
        r'var safetyMap_active     = false;',
        r'var safetyMap_active     = false;\n  var safetyMap_timeOfDay  = "day";\n  window.safetyMap_setTime = function(t) { safetyMap_timeOfDay = t; document.getElementById("sm-day-btn").style.color = (t==="day")?"#FACC15":"var(--text-muted)"; document.getElementById("sm-night-btn").style.color = (t==="night")?"#A78BFA":"var(--text-muted)"; if(safetyMap_active){ safetyMap_load(safetyMap_lastLat, safetyMap_lastLon); loadSafetyInsights(); } };\n  setTimeout(()=>window.safetyMap_setTime("day"),500);',
        content
    )

# 4. Modify URL fetching in safetyMap_load
content = re.sub(
    r"var url = '/api/safety-map/roads\?s=' \+ b\.s \+ '&w=' \+ b\.w \+ '&n=' \+ b\.n \+ '&e=' \+ b\.e;",
    r"var url = '/api/safety-map/roads?s=' + b.s + '&w=' + b.w + '&n=' + b.n + '&e=' + b.e + '&time=' + safetyMap_timeOfDay;",
    content
)

content = re.sub(
    r"fetch\(`/api/safety-insights/nearby\?lat=\$\{center\.lat\}&lon=\$\{center\.lng\}`\)",
    r"fetch(`/api/safety-insights/nearby?lat=${center.lat}&lon=${center.lng}&time=${safetyMap_timeOfDay}`)",
    content
)

# 5. Add action buttons to the factors HTML
action_btns = """
      <div style="margin-top: 12px; display: flex; flex-direction: column; gap: 6px;">
        <button onclick="document.getElementById('origin-input').value = '${road_name}'; switchSection('sec-search'); document.getElementById('origin-input').focus();" style="width: 100%; padding: 8px; background: rgba(59, 130, 246, 0.2); color: #60A5FA; border: 1px solid #3B82F6; border-radius: 6px; font-size: 11px; cursor: pointer;">📍 Set as Source</button>
        <button onclick="document.getElementById('dest-input').value = '${road_name}'; switchSection('sec-search'); document.getElementById('dest-input').focus();" style="width: 100%; padding: 8px; background: rgba(16, 185, 129, 0.2); color: #34D399; border: 1px solid #10B981; border-radius: 6px; font-size: 11px; cursor: pointer;">🏁 Set as Destination</button>
        <button onclick="switchSection('sec-feedback');" style="width: 100%; padding: 8px; background: rgba(239, 68, 68, 0.1); color: #F87171; border: 1px dashed #EF4444; border-radius: 6px; font-size: 11px; cursor: pointer;">⚠️ Report an Issue</button>
      </div>
"""

# Replace in safetyMap_showInfo
if "Set as Source" not in content:
    # the function is safetyMap_showInfo
    content = re.sub(
        r"(html \+= '<div style=\"margin-top:10px;font-size:10px;color:#64748B;\">Data Confidence: ' \+ feature\.confidence \+ '</div>';)",
        r"\1\n      html += `\n" + action_btns.replace("${road_name}", "${feature.name}") + r"\n      `;",
        content
    )
    
    # Also in showSafetyInsightDetails
    content = re.sub(
        r"(Last Updated: \$\{road\.last_updated\}\n      </div>)",
        r"\1\n" + action_btns.replace("${road_name}", "${road.name}"),
        content
    )


with open('backend/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
