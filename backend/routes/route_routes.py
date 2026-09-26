from flask import Blueprint, request, jsonify, current_app
from backend.services.routing_service import RoutingService
from backend.services.geocoding_service import GeocodingService
from backend.services.haven_service import LiveHavenService
from backend.services.safety_engine import SafetyScoringEngine
from backend.services.resilience_engine import SafetyResilienceEngine
from backend.services.environmental_service import EnvironmentalService
from backend.services.explanation_generator import ExplanationGenerator

route_bp = Blueprint('routes', __name__)


# ─────────────────────────────────────────────────────────────
# AUTOCOMPLETE  (for live search-as-you-type suggestions)
# ─────────────────────────────────────────────────────────────
@route_bp.route('/api/routes/autocomplete', methods=['GET'])
def autocomplete():
    q = request.args.get('q', '').strip()
    if len(q) < 3:
        return jsonify({'suggestions': []}), 200
    results = GeocodingService.autocomplete(q, limit=6)
    return jsonify({'suggestions': results}), 200


# ─────────────────────────────────────────────────────────────
# MAIN ROUTE COMPARISON  (real geocoding + real OSRM routing)
# ─────────────────────────────────────────────────────────────
@route_bp.route('/api/routes/compare', methods=['POST'])
def compare_routes():
    data              = request.get_json() or {}
    origin            = (data.get('origin') or '').strip()
    destination       = (data.get('destination') or '').strip()
    vehicle           = data.get('vehicle', 'personal_vehicle')
    departure_time    = data.get('departure_time', 'Now')
    safety_preference = data.get('safety_preference', 'balanced')
    # Frontend may pass pre-resolved coords; treat them as a hint only
    hint_origin_coords = data.get('user_coords')
    hint_dest_coords   = data.get('dest_coords')

    if not origin or not destination:
        return jsonify({'error': 'Both origin and destination are required.'}), 400

    demo_mode          = current_app.config.get('DEMO_MODE', False)
    threshold_seconds  = current_app.config.get('RESILIENCE_THRESHOLD_SECONDS', 120)

    # ── 1. Geocode origin ──────────────────────────────────────
    origin_coords = hint_origin_coords
    if not origin_coords:
        places = GeocodingService.search_place(origin, limit=1)
        if places:
            origin_coords = {"latitude": places[0]["latitude"], "longitude": places[0]["longitude"]}

    if not origin_coords:
        return jsonify({
            'error': f'Could not find the location "{origin}". '
                     'Please try a more specific address or landmark name.'
        }), 422

    # ── 2. Geocode destination ─────────────────────────────────
    dest_coords = hint_dest_coords
    if not dest_coords:
        places = GeocodingService.search_place(destination, limit=1)
        if places:
            dest_coords = {"latitude": places[0]["latitude"], "longitude": places[0]["longitude"]}

    if not dest_coords:
        return jsonify({
            'error': f'Could not find the location "{destination}". '
                     'Please try a more specific address or landmark name.'
        }), 422

    # ── 3. Safe havens around the mid-point ───────────────────
    mid_lat = (origin_coords['latitude']  + dest_coords['latitude'])  / 2.0
    mid_lon = (origin_coords['longitude'] + dest_coords['longitude']) / 2.0
    havens_list = LiveHavenService.get_havens_for_location(mid_lat, mid_lon, radius_km=4.0)

    # ── 4. Fetch real OSRM routes ─────────────────────────────
    routing_svc = RoutingService(demo_mode=demo_mode)
    raw_routes  = routing_svc.get_routes(
        origin_name   = origin,
        dest_name     = destination,
        origin_coords = origin_coords,
        dest_coords   = dest_coords,
        vehicle       = vehicle
    )

    if not raw_routes:
        return jsonify({
            'error': 'No routes could be calculated between these locations. '
                     'Check that both places exist and are reachable by road/foot.'
        }), 422

    # ── 5. Score every route ───────────────────────────────────
    safety_engine = SafetyScoringEngine()
    speed_mps = {"walking": 1.3, "bus": 2.5}.get(vehicle, 3.5)
    resilience_engine = SafetyResilienceEngine(
        default_threshold_seconds=threshold_seconds,
        travel_speed_mps=speed_mps
    )

    analyzed_routes = []
    for route in raw_routes:
        coords = route.get('coordinates', [])

        env_signals = EnvironmentalService.evaluate_corridor_signals(
            coordinates    = coords,
            vehicle        = vehicle,
            departure_time = departure_time
        )

        res_data = resilience_engine.analyze_route_resilience(
            route_coordinates = coords,
            safe_havens       = havens_list,
            threshold_seconds = threshold_seconds
        )

        safety_result = safety_engine.calculate_score(
            lighting           = env_signals["streetlights"]["score"],
            incidents          = env_signals["crime_safety"]["score"],
            foot_traffic       = env_signals["crowded_area"]["score"],
            emergency_services = env_signals["nearby_havens"]["score"],
            cctv_coverage      = env_signals["cctv_coverage"]["score"],
            departure_time     = departure_time,
            safety_preference  = safety_preference
        )

        analyzed_routes.append({
            "route_id":                  route.get("route_id", "route-1"),
            "name":                      route.get("name", "Route"),
            "vehicle":                   vehicle,
            "distance_km":               route.get("distance_km", 0),
            "duration_min":              route.get("duration_min", 0),
            "safety_score":              safety_result["safety_score"],
            "resilience_score":          res_data["resilience_score"],
            "max_time_to_haven_seconds": res_data["max_time_to_haven"],
            "avg_time_to_haven_seconds": res_data.get("avg_time_to_haven", 60),
            "havens_count":              max(1, res_data["havens_count"]),
            "threshold_seconds":         threshold_seconds,
            "meets_threshold":           res_data["meets_threshold"],
            "resilience_status":         res_data["resilience_status"],
            "lighting_score":            safety_result["lighting_score"],
            "foot_traffic_score":        safety_result["foot_traffic_score"],
            "incident_safety_score":     safety_result["incident_safety_score"],
            "emergency_proximity_score": safety_result["emergency_proximity_score"],
            "cctv_coverage_score":       safety_result.get("cctv_coverage_score", 85),
            "environmental_signals":     env_signals,
            "summary_badges":            env_signals.get("summary_badges", []),
            "confidence_level":          safety_result["confidence_level"],
            "coordinates":               coords,
            "steps":                     route.get("steps", []),
            "is_recommended":            route.get("is_recommended", False),
            "tradeoff":                  route.get("tradeoff", ""),
            "explanations":              route.get("explanations", [])
        })

    # ── 6. Ensure exactly one recommended route ───────────────
    if not any(r.get("is_recommended") for r in analyzed_routes):
        analyzed_routes.sort(
            key=lambda r: (r["safety_score"], r["resilience_score"]),
            reverse=True
        )
        analyzed_routes[0]["is_recommended"] = True

    # ── 7. Generate "Why this route?" explanation ─────────────
    primary   = next((r for r in analyzed_routes if r.get("is_recommended")), analyzed_routes[0])
    alternates = [r for r in analyzed_routes if r is not primary]

    if not primary.get("explanations"):
        exp = ExplanationGenerator.generate_explanations(primary, alternates)
        primary["explanations"] = exp["why_this_route"]
        primary["tradeoff"]     = exp["tradeoff"]

    return jsonify({
        "success":         True,
        "origin":          origin,
        "destination":     destination,
        "origin_coords":   origin_coords,
        "dest_coords":     dest_coords,
        "departure_time":  departure_time,
        "safety_preference": safety_preference,
        "routes":          analyzed_routes,
        "safe_havens":     havens_list,
        "live_routing":    True,
        "disclaimer":      (
            "Safety scores are advisory estimates based on environmental signals. "
            "Always stay alert and trust your instincts."
        )
    }), 200
