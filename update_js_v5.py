import re

with open('backend/templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# JS logic to update safetyMap_drawRoads and safetyMap_openPanel
new_js_logic = """
  var safetyMap_selectedPolyline = null;
  var isColorblindMode = false;

  window.toggleColorblindMode = function(enabled) {
    isColorblindMode = enabled;
    if (typeof currentColorPalette !== 'undefined') {
      currentColorPalette = enabled ? SAFETY_COLORS_COLORBLIND : SAFETY_COLORS_STANDARD;
    }
    // Update legend swatches
    const container = document.getElementById('legend-swatches');
    if (container) {
      const p = currentColorPalette;
      container.innerHTML = `
        <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:${p.very_safe.hex};margin-right:7px;vertical-align:middle;"></span>🟢 80–100 Very Safe</span>
        <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:${p.safe.hex};margin-right:7px;vertical-align:middle;"></span>🟢 60–79 Safe</span>
        <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:${p.moderate.hex};margin-right:7px;vertical-align:middle;"></span>🟡 40–59 Moderate</span>
        <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:${p.risky.hex};margin-right:7px;vertical-align:middle;"></span>🟠 20–39 Risky</span>
        <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:${p.unsafe.hex};margin-right:7px;vertical-align:middle;"></span>🔴 0–19 Unsafe</span>
        <span><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:${p.nodata.hex};margin-right:7px;vertical-align:middle;"></span>⚪ No data (Dashed)</span>
      `;
    }
    if (safetyMap_active) safetyMap_loadBounds();
  };

  function safetyMap_drawRoads(roads) {
    if (typeof map === 'undefined' || !map) return;
    var newGroup = L.layerGroup();

    roads.forEach(function(road) {
      if (!road.geometry || road.geometry.length < 2) return;

      var isLowData = (road.confidence && road.confidence.toUpperCase() === 'LOW') || road.colour === '#9AA0A6';
      var roadColor = road.colour;

      if (isColorblindMode && typeof getSafetyColorInfo === 'function') {
        roadColor = getSafetyColorInfo(road.safety_score, isLowData).hex;
      }

      var lineWeight = (road.highway === 'primary' || road.highway === 'trunk' || road.highway === 'motorway') ? 5 : 3;

      // 1. Thin white casing underneath for visibility on any map tile
      L.polyline(road.geometry, {
        color: '#FFFFFF',
        weight: lineWeight + 3,
        opacity: 0.85,
        interactive: false
      }).addTo(newGroup);

      // 2. Main colored safety line
      var line = L.polyline(road.geometry, {
        color: roadColor,
        weight: lineWeight,
        opacity: 0.95,
        dashArray: isLowData ? '6, 6' : null,
        lineCap: 'round',
        lineJoin: 'round',
        interactive: true
      });

      line.on('mouseover', function() { line.setStyle({ weight: lineWeight + 3 }); });
      line.on('mouseout', function() { if (safetyMap_selectedPolyline !== line) line.setStyle({ weight: lineWeight }); });

      (function(r, poly) {
        poly.on('click', function(e) {
          L.DomEvent.stopPropagation(e);
          if (safetyMap_selectedPolyline) {
            safetyMap_selectedPolyline.setStyle({ weight: 4, color: safetyMap_selectedPolyline._origColor });
          }
          safetyMap_selectedPolyline = poly;
          poly._origColor = roadColor;
          poly.setStyle({ weight: 8, color: '#FFFFFF' });
          safetyMap_openPanel(r);
        });
      })(road, line);

      line.addTo(newGroup);
    });

    if (safetyMap_layerGroup) map.removeLayer(safetyMap_layerGroup);
    safetyMap_layerGroup = newGroup;
    map.addLayer(safetyMap_layerGroup);
  }

  function safetyMap_openPanel(road) {
    var panel   = document.getElementById('safety-info-panel');
    var title   = document.getElementById('safety-info-title');
    var score   = document.getElementById('safety-info-score');
    var risk    = document.getElementById('safety-info-risk');
    var conf    = document.getElementById('safety-info-confidence');
    var details = document.getElementById('safety-info-details');
    if (!panel) return;

    var roadColor = road.colour;
    if (isColorblindMode && typeof getSafetyColorInfo === 'function') {
      roadColor = getSafetyColorInfo(road.safety_score, road.confidence === 'LOW').hex;
    }

    title.textContent = road.name || (road.highway ? road.highway.toUpperCase() + ' Road' : 'Road Segment');
    score.textContent = (road.safety_score !== undefined && road.safety_score !== null) ? road.safety_score + '/100' : 'N/A';
    score.style.color = roadColor;
    risk.textContent  = road.risk_label || 'Evaluated Segment';
    conf.textContent  = (road.confidence || 'Medium') + ' Confidence';

    var html = '';
    
    // Plain-language reasons section ("Why this score")
    html += '<div style="margin-top:12px; padding-top:10px; border-top:1px solid #334155;">';
    html += '<div style="font-size:11px; font-weight:700; color:#A78BFA; margin-bottom:8px;">💡 WHY THIS SCORE:</div>';
    
    if (road.reasons && road.reasons.length > 0) {
      road.reasons.forEach(function(r) {
        var badgeColor = r.is_negative ? '#EF4444' : '#22C55E';
        var icon = r.is_negative ? '⚠️' : '✅';
        html += '<div style="display:flex; align-items:flex-start; gap:6px; margin-bottom:6px; font-size:11px; color:#E2E8F0;">';
        html += '<span>' + icon + '</span>';
        html += '<div><b style="color:' + badgeColor + ';">' + r.factor + ':</b> ' + r.text + '</div>';
        html += '</div>';
      });
    } else if (road.factors) {
      html += '<div style="font-size:11px; color:#CBD5E1;">';
      html += '<div>💡 Lighting: ' + (road.factors.lighting || 'N/A') + '/100</div>';
      html += '<div>🛡️ Crime Safety: ' + (road.factors.crime_safety || 'N/A') + '/100</div>';
      html += '<div>👥 Night Footfall: ' + (road.factors.foot_traffic || 'N/A') + '/100</div>';
      html += '<div>📷 CCTV Coverage: ' + (road.factors.cctv_coverage || 'N/A') + '/100</div>';
      html += '</div>';
    }

    html += '</div>';

    // Action buttons
    var rName = (road.name || 'Selected Location').replace(/'/g, "\\'");
    html += `
      <div style="margin-top: 14px; display: flex; flex-direction: column; gap: 6px;">
        <button onclick="document.getElementById('origin-input').value='${rName}'; switchSection('sec-search');" style="width:100%; padding:8px; background:rgba(59,130,246,0.2); color:#60A5FA; border:1px solid #3B82F6; border-radius:6px; font-size:11px; font-weight:600; cursor:pointer;">📍 Set as Source</button>
        <button onclick="document.getElementById('dest-input').value='${rName}'; switchSection('sec-search');" style="width:100%; padding:8px; background:rgba(16,185,129,0.2); color:#34D399; border:1px solid #10B981; border-radius:6px; font-size:11px; font-weight:600; cursor:pointer;">🏁 Set as Destination</button>
        <button onclick="switchSection('sec-feedback');" style="width:100%; padding:8px; background:rgba(239,68,68,0.1); color:#F87171; border:1px dashed #EF4444; border-radius:6px; font-size:11px; font-weight:600; cursor:pointer;">⚠️ Report an Issue</button>
      </div>
    `;

    details.innerHTML = html;
    panel.style.display = 'block';
  }
"""

# Replace safetyMap_drawRoads and safetyMap_openPanel in html
html = re.sub(r'function safetyMap_drawRoads[\s\S]*?function safetyMap_closePanel', new_js_logic + '\n  function safetyMap_closePanel', html)

with open('backend/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated JS drawing and popup panel logic.")
