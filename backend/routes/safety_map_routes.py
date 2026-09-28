"""
Safety Map Mode API Routes — NEW FILE (do not modify existing routes).
Provides real-time road-segment safety heatmap data around a GPS location,
reusing the existing SafetyScoringEngine + EnvironmentalService pipeline.
"""

import math
from flask import Blueprint, request, jsonify
from backend.services.safety_engine import SafetyScoringEngine
from backend.services.environmental_service import EnvironmentalService

safety_map_bp = Blueprint('safety_map', __name__, url_prefix='/api/safety-map')

# Module-level cache: { (round(lat,3), round(lon,3)): {"data": ..., "ts": float} }
_SEGMENT_CACHE: dict = {}
_CACHE_TTL_SECONDS = 300  # 5 minutes

import time as _time

# Singleton scoring engine (reuse existing algorithm — do NOT recreate)
_scoring_engine = SafetyScoringEngine()


def _haversine_offset(lat: float, lon: float, dx_m: float, dy_m: float):
    """Return (lat, lon) displaced by dx_m east and dy_m north from origin."""
    R = 6371000.0
    new_lat = lat + (dy_m / R) * (180 / math.pi)
    new_lon = lon + (dx_m / (R * math.cos(math.radians(lat)))) * (180 / math.pi)
    return round(new_lat, 6), round(new_lon, 6)


def _score_for_point(lat: float, lon: float):
    """
    Run the full EnvironmentalService → SafetyScoringEngine pipeline for a
    single centroid point.  Results are cached at 3-decimal precision.
    """
    cache_key = (round(lat, 3), round(lon, 3))
    now = _time.time()

    if cache_key in _SEGMENT_CACHE:
        entry = _SEGMENT_CACHE[cache_key]
        if now - entry["ts"] < _CACHE_TTL_SECONDS:
            return entry["data"]

    # Wrap single point as corridor expected by EnvironmentalService
    coords = [{"latitude": lat, "longitude": lon}]

    try:
        env_signals = EnvironmentalService.evaluate_corridor_signals(
            coordinates=coords,
            vehicle="walking",
            departure_time=None,
            corridor_name="Safety Map Segment"
        )
    except Exception as exc:
        print(f"[SafetyMap] EnvironmentalService error: {exc}")
        env_signals = EnvironmentalService._get_default_signals()

    # Map env signals → engine inputs
    lighting_score    = env_signals.get("streetlights", {}).get("score", 65)
    crime_score       = env_signals.get("crime_safety", {}).get("score", 80)
    crowd_score       = env_signals.get("crowded_area", {}).get("score", 70)
    cctv_score        = env_signals.get("cctv_coverage", {}).get("score", 70)
    haven_score       = env_signals.get("nearby_havens", {}).get("score", 75)

    try:
        result = _scoring_engine.calculate_score(
            lighting=float(lighting_score),
            incidents=float(crime_score),
            foot_traffic=float(crowd_score),
            emergency_services=float(haven_score),
            cctv_coverage=float(cctv_score),
        )
    except Exception as exc:
        print(f"[SafetyMap] ScoringEngine error: {exc}")
        result = {
            "safety_score": 70,
            "safety_level": "MEDIUM",
            "confidence_level": "LOW",
        }

    score = result.get("safety_score", 70)
    level = result.get("safety_level", "MEDIUM")
    confidence = result.get("confidence_level", "MEDIUM")

    # Colour coding
    if score >= 75:
        colour = "#22C55E"   # green — lower risk
        risk_label = "Lower Risk"
    elif score >= 55:
        colour = "#F59E0B"   # amber — moderate risk
        risk_label = "Moderate Risk"
    else:
        colour = "#EF4444"   # red — higher risk
        risk_label = "Higher Risk"

    data = {
        "lat": lat,
        "lon": lon,
        "safety_score": score,
        "safety_level": level,
        "risk_label": risk_label,
        "colour": colour,
        "confidence": confidence,
        "factors": {
            "lighting": lighting_score,
            "crime_safety": crime_score,
            "foot_traffic": crowd_score,
            "cctv_coverage": cctv_score,
            "safe_havens": haven_score,
        },
        "summary_badges": env_signals.get("summary_badges", []),
    }

    _SEGMENT_CACHE[cache_key] = {"data": data, "ts": now}
    return data


@safety_map_bp.route('/segments', methods=['GET'])
def get_safety_segments():
    """
    GET /api/safety-map/segments?lat=<lat>&lon=<lon>&radius_km=<r>

    Returns a grid of safety-scored points around the given GPS location.
    Each point represents a ~150 m road-segment centroid.
    """
    try:
        lat = float(request.args.get('lat', 0))
        lon = float(request.args.get('lon', 0))
        radius_km = float(request.args.get('radius_km', 0.6))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid parameters. Provide lat, lon, and optional radius_km."}), 400

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return jsonify({"error": "Coordinates out of range."}), 400

    # Clamp radius
    radius_km = max(0.2, min(1.5, radius_km))
    radius_m = radius_km * 1000

    # Build a grid of sample points (step ~150 m)
    step_m = 150
    points = []
    steps = int(radius_m / step_m)

    for i in range(-steps, steps + 1):
        for j in range(-steps, steps + 1):
            dx = j * step_m
            dy = i * step_m
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > radius_m:
                continue
            p_lat, p_lon = _haversine_offset(lat, lon, dx, dy)
            points.append((p_lat, p_lon))

    if not points:
        return jsonify({"error": "No points generated. Check radius parameter."}), 400

    # Limit to avoid overloading Overpass API
    # Score unique cache-key points only
    unique: dict = {}
    for p_lat, p_lon in points:
        ck = (round(p_lat, 3), round(p_lon, 3))
        if ck not in unique:
            unique[ck] = (p_lat, p_lon)

    segments = []
    for (p_lat, p_lon) in unique.values():
        seg = _score_for_point(p_lat, p_lon)
        segments.append(seg)

    return jsonify({
        "segments": segments,
        "count": len(segments),
        "center": {"lat": lat, "lon": lon},
        "radius_km": radius_km
    })
