from flask import Blueprint, request, jsonify
from backend.models.models import SafeHaven
from backend.utils.geo_helper import haversine_distance_km

haven_bp = Blueprint('havens', __name__)

@haven_bp.route('/api/havens/nearby', methods=['GET'])
def get_nearby_havens():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius_km = request.args.get('radius_km', default=5.0, type=float)
    haven_type = request.args.get('type')

    query = SafeHaven.query
    if haven_type:
        query = query.filter_by(type=haven_type)

    all_havens = query.all()
    results = []

    for h in all_havens:
        data = h.to_dict()
        if lat is not None and lon is not None:
            dist_km = haversine_distance_km(lat, lon, h.latitude, h.longitude)
            if dist_km <= radius_km:
                data['distance_km'] = round(dist_km, 2)
                data['distance_meters'] = int(round(dist_km * 1000))
                results.append(data)
        else:
            results.append(data)

    if lat is not None and lon is not None:
        results.sort(key=lambda x: x.get('distance_km', 999))

    return jsonify({
        'success': True,
        'count': len(results),
        'havens': results
    }), 200
