from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any, List
from backend.config import Config
from backend.services.routing_service import RoutingService
from backend.services.safety_engine import SafetyScoringEngine
from backend.services.environmental_service import EnvironmentalService
from backend.services.resilience_engine import SafetyResilienceEngine
from backend.services.haven_service import LiveHavenService
from backend.services.geocoding_service import GeocodingService

route_bp = Blueprint('route_bp', __name__)

@route_bp.route('/api/routes/autocomplete', methods=['GET'])
def autocomplete():
    """Autocomplete search endpoint for origin and destination input fields."""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'suggestions': []}), 200

    places = GeocodingService.search_place(query, limit=5)
    suggestions = [
        {
            'display_name': p.get('display_name', query),
            'latitude': p.get('latitude', 0.0),
            'longitude': p.get('longitude', 0.0)
        }
        for p in places
    ]
    return jsonify({'suggestions': suggestions}), 200


@route_bp.route('/api/routes/calculate', methods=['POST'])
def calculate_routes():
    """
    PRIMARY STAGE 1 + STAGE 2 ROUTE PIPELINE ENDPOINT
    
    Input JSON:
    {
        "origin": { "lat": 10.7905, "lng": 78.7047 } OR "College Gate",
        "destination": { "lat": 10.7950, "lng": 78.7100 } OR "Central Library",
        "travel_mode": "walking",
        "safety_preference": "balanced"
    }
    """
    data = request.get_json() or {}
    
    origin_raw = data.get('origin')
    dest_raw = data.get('destination')
    travel_mode = data.get('travel_mode') or data.get('vehicle') or "walking"
    safety_preference = data.get('safety_preference') or "balanced"
    departure_time = data.get('departure_time') or "Now"

    # Resolve Origin Coordinates
    o_lat, o_lng = None, None
    if isinstance(origin_raw, dict):
        o_lat = origin_raw.get('lat') or origin_raw.get('latitude')
        o_lng = origin_raw.get('lng') or origin_raw.get('longitude')
    elif isinstance(origin_raw, str) and origin_raw.strip():
        places = GeocodingService.search_place(origin_raw.strip(), limit=1)
        if places:
            o_lat, o_lng = places[0]['latitude'], places[0]['longitude']

    if o_lat is None or o_lng is None:
        return jsonify({'error': 'Valid origin coordinates or location name required.'}), 400

    # Resolve Destination Coordinates
    d_lat, d_lng = None, None
    if isinstance(dest_raw, dict):
        d_lat = dest_raw.get('lat') or dest_raw.get('latitude')
        d_lng = dest_raw.get('lng') or dest_raw.get('longitude')
    elif isinstance(dest_raw, str) and dest_raw.strip():
        places = GeocodingService.search_place(dest_raw.strip(), limit=1)
        if places:
            d_lat, d_lng = places[0]['latitude'], places[0]['longitude']

    if d_lat is None or d_lng is None:
        return jsonify({'error': 'Valid destination coordinates or location name required.'}), 400

    # ── STAGE 1: ROUTE GENERATION (OSRM / GOOGLE) ─────────────
    routing_svc = RoutingService()
    stage1_result = routing_svc.get_candidate_routes(
        origin_lat=o_lat,
        origin_lng=o_lng,
        dest_lat=d_lat,
        dest_lng=d_lng,
        travel_mode=travel_mode
    )

    if stage1_result.get("already_at_destination"):
        arr_route = stage1_result["routes"][0]
        arr_route["safety_score"] = 99
        arr_route["safety_level"] = "HIGH"
        return jsonify({
            "success": True,
            "already_at_destination": True,
            "recommended_route": arr_route,
            "alternatives": [],
            "routing_provider": stage1_result.get("routing_provider", "OSRM"),
            "safety_model": "xgboost_trained",
            "data_quality": "HIGH"
        }), 200

    raw_candidate_routes = stage1_result.get("routes", [])
    if not raw_candidate_routes:
        return jsonify({
            "error": "No physical route found between these locations. Check coordinates or travel mode."
        }), 422

    # ── STAGE 2: SAFETY SCORING & REAL-TIME ANALYSIS ─────────
    mid_lat = (o_lat + d_lat) / 2.0
    mid_lon = (o_lng + d_lng) / 2.0
    havens_list = LiveHavenService.get_havens_for_location(mid_lat, mid_lon, radius_km=4.0)

    safety_engine = SafetyScoringEngine()
    threshold_seconds = Config.RESILIENCE_THRESHOLD_SECONDS
    speed_mps = {"walking": 1.3, "bike": 4.0, "bus": 3.0}.get(travel_mode, 4.5)
    resilience_engine = SafetyResilienceEngine(default_threshold_seconds=threshold_seconds, travel_speed_mps=speed_mps)

    scored_routes = []
    min_duration_sec = min(r.get("duration_sec", 60) for r in raw_candidate_routes) or 60

    last_env_signals = None

    for idx, route in enumerate(raw_candidate_routes):
        coords = route.get("coordinates", [])

        # Collect Environmental & Real-Time Features
        env_signals = EnvironmentalService.evaluate_corridor_signals(
            coordinates=coords,
            vehicle=travel_mode,
            departure_time=departure_time,
            corridor_name=route.get("name", "")
        )
        last_env_signals = env_signals

        # Calculate Resilience
        res_data = resilience_engine.analyze_route_resilience(
            route_coordinates=coords,
            safe_havens=havens_list,
            threshold_seconds=threshold_seconds
        )

        # XGBoost Model Safety Prediction
        safety_eval = safety_engine.calculate_score(
            lighting=env_signals["streetlights"]["score"],
            incidents=env_signals["crime_safety"]["score"],
            foot_traffic=env_signals["crowded_area"]["score"],
            emergency_services=env_signals["nearby_havens"]["score"],
            cctv_coverage=env_signals["cctv_coverage"]["score"],
            police_patrol=env_signals.get("police_patrol", {}).get("score", 78),
            road_condition=env_signals.get("road_condition", {}).get("score", 75),
            accident_rate_safety=env_signals.get("accident_safety", {}).get("score", 82),
            resilience_reach_time=res_data["max_time_to_haven"],
            departure_time=departure_time,
            safety_preference=safety_preference
        )

        safety_score = safety_eval["safety_score"]
        dur_sec = route.get("duration_sec", 60)
        dur_ratio = dur_sec / min_duration_sec

        # Trade-off selection score calculation
        time_penalty = 0.0
        if dur_ratio > Config.MAX_TIME_PENALTY_RATIO:
            time_penalty = (dur_ratio - Config.MAX_TIME_PENALTY_RATIO) * 25.0

        if safety_preference == "fastest":
            selection_score = (100.0 / (dur_sec / 60.0 + 1)) + (safety_score * 0.2)
        elif safety_preference == "safest":
            selection_score = safety_score - time_penalty
        else: # balanced
            selection_score = (safety_score * Config.ROUTE_SELECTION_SAFETY_WEIGHT) - (time_penalty * 0.5)

        scored_routes.append({
            "route_id": route.get("route_id", f"route-{idx+1}"),
            "name": route.get("name", f"Candidate Corridor {idx+1}"),
            "travel_mode": travel_mode,
            "distance_m": route.get("distance_m", 0),
            "distance_km": route.get("distance_km", 0),
            "duration_sec": dur_sec,
            "duration_min": route.get("duration_min", 1),
            "duration_minutes": route.get("duration_min", 1),
            "safety_score": safety_score,
            "safety_level": safety_eval["safety_level"],
            "selection_score": round(selection_score, 2),
            "resilience_score": res_data["resilience_score"],
            "max_time_to_haven_seconds": res_data["max_time_to_haven"],
            "resilience_status": res_data["resilience_status"],
            "metrics": {
                "nearest_police_m": res_data.get("nearest_police_m", 420),
                "nearest_hospital_m": res_data.get("nearest_hospital_m", 680),
                "max_help_distance_m": res_data.get("maximum_help_distance_m", 850),
                "avg_help_distance_m": res_data.get("average_help_distance_m", 390),
                "percent_within_help_threshold": res_data.get("percent_within_threshold", 100.0)
            },
            "lighting_score": env_signals["streetlights"]["score"],
            "lighting_status": env_signals["streetlights"]["status"],
            "foot_traffic_score": env_signals["crowded_area"]["score"],
            "foot_traffic_status": env_signals["crowded_area"]["status"],
            "incident_safety_score": env_signals["crime_safety"]["score"],
            "incident_safety_status": env_signals["crime_safety"]["status"],
            "cctv_coverage_score": env_signals["cctv_coverage"]["score"],
            "cctv_coverage_status": env_signals["cctv_coverage"]["status"],
            "havens_count": res_data.get("havens_count", 1),
            "safety_model": safety_eval["safety_model"],
            "data_quality": safety_eval["data_quality"],
            "data_quality_adjustment": safety_eval["data_quality_adjustment"],
            "xgboost_feature_importances": safety_eval["xgboost_feature_importances"],
            "coordinates": coords,
            "steps": route.get("steps", []),
            "tradeoff_notes": f"Safety Score: {safety_score}/100 • Reach Time: {res_data['max_time_to_haven']}s"
        })

    # Sort routes by trade-off selection score
    scored_routes.sort(key=lambda r: r["selection_score"], reverse=True)

    recommended = scored_routes[0]
    recommended["is_recommended"] = True

    alternatives = scored_routes[1:] if len(scored_routes) > 1 else []
    for a in alternatives:
        a["is_recommended"] = False

    return jsonify({
        "success": True,
        "already_at_destination": False,
        "recommended_route": recommended,
        "alternatives": alternatives,
        "routes": scored_routes,
        "routing_provider": stage1_result.get("routing_provider", "OSRM"),
        "safety_model": recommended["safety_model"],
        "data_quality": recommended["data_quality"],
        "realtime_metadata": last_env_signals.get("realtime_metadata") if last_env_signals else {},
        "live_weather": last_env_signals.get("live_weather") if last_env_signals else {}
    }), 200


@route_bp.route('/api/routes/compare', methods=['POST'])
def compare_routes_legacy():
    return calculate_routes()
