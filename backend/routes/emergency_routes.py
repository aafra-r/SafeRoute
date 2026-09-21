from flask import Blueprint, request, jsonify
from backend.services.emergency_service import EmergencyService
from backend.models.models import User, EmergencyContact, TrustedContact
from backend.database.db import db

emergency_bp = Blueprint('emergency', __name__)

@emergency_bp.route('/api/emergency/nearest-haven', methods=['POST'])
def find_nearest_haven():
    data = request.get_json() or {}
    lat = data.get('latitude')
    lon = data.get('longitude')

    if lat is None or lon is None:
        return jsonify({'error': 'latitude and longitude are required'}), 400

    result = EmergencyService.get_nearest_safe_haven(lat, lon)
    return jsonify({
        'success': True,
        'data': result
    }), 200

@emergency_bp.route('/api/emergency/share-location', methods=['POST'])
def share_location():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    lat = data.get('latitude', 12.9780)
    lon = data.get('longitude', 77.6010)
    destination = data.get('destination', 'Central Library')
    nearest_haven_name = data.get('nearest_haven_name', 'City General Hospital')

    user = db.session.get(User, user_id) if user_id else None
    user_name = user.full_name if user else "SafeRoute User"

    contacts = []
    if user and user.emergency_contacts:
        contacts = [c.to_dict() for c in user.emergency_contacts]
    else:
        contacts = [
            {"name": "Sarah Rivera (Emergency Contact)", "phone": "+1 (555) 019-9988"},
            {"name": "Campus Security Dispatch", "phone": "+1 (555) 019-1122"}
        ]

    result = EmergencyService.simulate_location_share(
        user_name=user_name,
        current_lat=lat,
        current_lon=lon,
        destination=destination,
        nearest_haven_name=nearest_haven_name,
        contacts=contacts
    )

    return jsonify(result), 200
