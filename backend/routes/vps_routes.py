"""
Visual Positioning System (VPS) & 360° Visual View API Routes for SafeRoute.
"""
from flask import Blueprint, request, jsonify
from backend.services.vps_service import VPSService

vps_bp = Blueprint('vps', __name__, url_prefix='/api/vps')

@vps_bp.route('/metadata', methods=['GET', 'POST'])
def get_vps_metadata():
    """
    Check 360° Street View metadata availability and returns panorama orientation info.
    Supports GET params (?lat=..&lon=..) and POST JSON ({latitude, longitude}).
    """
    if request.method == 'POST':
        data = request.get_json() or {}
        lat = data.get('latitude', data.get('lat'))
        lon = data.get('longitude', data.get('lon', data.get('lng')))
        heading = float(data.get('heading', 0.0))
        pitch = float(data.get('pitch', 0.0))
    else:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', request.args.get('lng'), type=float)
        heading = request.args.get('heading', default=0.0, type=float)
        pitch = request.args.get('pitch', default=0.0, type=float)

    if lat is None or lon is None:
        return jsonify({
            "error": "Missing latitude or longitude parameters",
            "available": False,
            "status": "INVALID_PARAMS"
        }), 400

    try:
        metadata = VPSService.get_streetview_metadata(lat, lon)
        embed_url = VPSService.get_panorama_embed_url(lat, lon, heading=heading, pitch=pitch)
        google_pano_url = VPSService.get_google_pano_url(lat, lon, heading=heading)
        metadata["embed_url"] = embed_url
        metadata["google_pano_url"] = google_pano_url
        metadata["heading"] = heading
        metadata["pitch"] = pitch
        return jsonify(metadata), 200
    except Exception as e:
        return jsonify({
            "error": str(e),
            "available": False,
            "status": "ERROR",
            "message": "360° visual coverage is unavailable at this location due to a service error."
        }), 500

@vps_bp.route('/embed-url', methods=['GET'])
def get_vps_embed_url():
    """
    Returns direct 360° Google Street View embed URL for coordinates.
    """
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', request.args.get('lng'), type=float)
    heading = request.args.get('heading', default=0.0, type=float)
    pitch = request.args.get('pitch', default=0.0, type=float)

    if lat is None or lon is None:
        return jsonify({"error": "Missing lat or lon parameters"}), 400

    embed_url = VPSService.get_panorama_embed_url(lat, lon, heading=heading, pitch=pitch)
    return jsonify({
        "embed_url": embed_url,
        "latitude": lat,
        "longitude": lon,
        "heading": heading,
        "pitch": pitch
    }), 200
