import re

with open('backend/templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

real_roads_client_js = """
  function safetyMap_getMockRoads(b) {
    return [
      {
        id: 5001, name: "Bharathidasan Salai", highway: "primary",
        geometry: [[10.8050, 78.6850], [10.7980, 78.6910], [10.7920, 78.7020], [10.7880, 78.7090]],
        safety_score: 90, colour: "#1B9E4B", risk_label: "Very Safe", confidence: "High",
        reasons: [{ factor: "Street Lighting", status: "good", text: "Well-lit primary avenue", is_negative: false }]
      },
      {
        id: 5002, name: "Tiruchirappalli - Pudukkottai Road (NH336)", highway: "trunk",
        geometry: [[10.8120, 78.6940], [10.8010, 78.6980], [10.7920, 78.7020], [10.7810, 78.7060], [10.7680, 78.7120]],
        safety_score: 85, colour: "#1B9E4B", risk_label: "Very Safe", confidence: "High",
        reasons: [{ factor: "CCTV Surveillance", status: "good", text: "Active CCTV coverage on highway", is_negative: false }]
      },
      {
        id: 5003, name: "Collectorate / Heber Road", highway: "primary",
        geometry: [[10.8150, 78.6820], [10.8080, 78.6860], [10.7980, 78.6910], [10.7890, 78.6950]],
        safety_score: 74, colour: "#7ACB5A", risk_label: "Safe", confidence: "High",
        reasons: [{ factor: "Emergency Services", status: "good", text: "Police station nearby (<0.5 km)", is_negative: false }]
      },
      {
        id: 5004, name: "Rockfort / West Boulevard Road", highway: "secondary",
        geometry: [[10.8280, 78.6950], [10.8220, 78.6970], [10.8120, 78.6940], [10.8050, 78.6850]],
        safety_score: 54, colour: "#F5D33F", risk_label: "Moderate", confidence: "Medium",
        reasons: [{ factor: "Night Footfall", status: "moderate", text: "Moderate crowd movement at night", is_negative: false }]
      },
      {
        id: 5005, name: "Mathur Road", highway: "secondary",
        geometry: [[10.7880, 78.7090], [10.7780, 78.7010], [10.7650, 78.6920], [10.7550, 78.6850]],
        safety_score: 48, colour: "#F5D33F", risk_label: "Moderate", confidence: "Medium",
        reasons: [{ factor: "Street Lighting", status: "moderate", text: "Moderate streetlight density", is_negative: false }]
      },
      {
        id: 5006, name: "Kamarajar Salai", highway: "tertiary",
        geometry: [[10.8010, 78.6980], [10.7950, 78.6920], [10.7890, 78.6950]],
        safety_score: 34, colour: "#F28C28", risk_label: "Risky", confidence: "Medium",
        reasons: [{ factor: "Street Lighting", status: "poor", text: "Poor street lighting in segment", is_negative: true }]
      },
      {
        id: 5007, name: "Anna Nagar Main Road", highway: "residential",
        geometry: [[10.7920, 78.7020], [10.7900, 78.6980], [10.7860, 78.6940]],
        safety_score: 18, colour: "#D62828", risk_label: "Unsafe", confidence: "Medium",
        reasons: [{ factor: "Night Footfall", status: "poor", text: "Low footfall and few open shops", is_negative: true }]
      },
      {
        id: 5008, name: "Srirangam Link Expressway", highway: "trunk",
        geometry: [[10.8520, 78.6920], [10.8410, 78.6930], [10.8280, 78.6950]],
        safety_score: 92, colour: "#1B9E4B", risk_label: "Very Safe", confidence: "High",
        reasons: [{ factor: "Crime Safety", status: "good", text: "High safety rating recorded", is_negative: false }]
      },
      {
        id: 5009, name: "TVS Tollgate / Airport Road", highway: "primary",
        geometry: [[10.7980, 78.6910], [10.7850, 78.7000], [10.7720, 78.7100]],
        safety_score: 82, colour: "#1B9E4B", risk_label: "Very Safe", confidence: "High",
        reasons: [{ factor: "Emergency Services", status: "good", text: "Hospital within 0.6 km", is_negative: false }]
      },
      {
        id: 5010, name: "Thillai Nagar Main Road", highway: "secondary",
        geometry: [[10.8220, 78.6850], [10.8150, 78.6820], [10.8080, 78.6860]],
        safety_score: 72, colour: "#7ACB5A", risk_label: "Safe", confidence: "High",
        reasons: [{ factor: "Night Footfall", status: "good", text: "Active commercial street", is_negative: false }]
      },
      {
        id: 5011, name: "Junction Station Road", highway: "tertiary",
        geometry: [[10.7950, 78.6820], [10.7910, 78.6860], [10.7880, 78.6910]],
        safety_score: 38, colour: "#F28C28", risk_label: "Risky", confidence: "Medium",
        reasons: [{ factor: "Crime Safety", status: "poor", text: "Elevated incident risk nearby", is_negative: true }]
      },
      {
        id: 5012, name: "Palakkarai Main Street", highway: "unclassified",
        geometry: [[10.8120, 78.6940], [10.8080, 78.6900], [10.8010, 78.6980]],
        safety_score: 28, colour: "#F28C28", risk_label: "Risky", confidence: "Medium",
        reasons: [{ factor: "Street Lighting", status: "poor", text: "Low lamp density along street", is_negative: true }]
      },
      {
        id: 5013, name: "Service Lane 4B", highway: "service",
        geometry: [[10.7860, 78.6940], [10.7820, 78.6900], [10.7780, 78.7010]],
        safety_score: 14, colour: "#D62828", risk_label: "Unsafe", confidence: "Medium",
        reasons: [{ factor: "CCTV Surveillance", status: "poor", text: "No surveillance cameras found", is_negative: true }]
      }
    ];
  }
"""

html = re.sub(r'function safetyMap_getMockRoads\(b\) \{[\s\S]*?\}\n  function safetyMap_drawRoads', real_roads_client_js + '\n  function safetyMap_drawRoads', html)

with open('backend/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated client-side mock roads to real curved Trichy road geometries.")
