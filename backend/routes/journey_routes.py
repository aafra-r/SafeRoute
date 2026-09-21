import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app
from backend.database.db import db
from backend.models.models import Journey, Route, SafeHaven, User
from backend.services.emergency_service import EmergencyService
from backend.utils.geo_helper import min_distance_to_route_meters

journey_bp = Blueprint('journeys', __name__)

@journey_bp.route('/api/journeys', methods=['POST'])
def start_journey():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    origin = data.get('origin', 'Current Location')
    destination = data.get('destination', 'Destination')
    vehicle = data.get('vehicle', 'walking')
    departure_time = data.get('departure_time', 'Now')
    distance = data.get('distance_km', 0.0)
    duration = data.get('duration_min', 0)
    safety_score = data.get('safety_score', 85)
    resilience_score = data.get('resilience_score', 90)
    max_time_to_haven = data.get('max_time_to_haven_seconds', 108)
    coordinates = data.get('coordinates', [])

    journey = Journey(
        user_id=user_id,
        origin=origin,
        destination=destination,
        vehicle=vehicle,
        departure_time=departure_time,
        distance=distance,
        duration=duration,
        safety_score=safety_score,
        resilience_score=resilience_score,
        max_time_to_haven=max_time_to_haven,
        status='IN_PROGRESS'
    )
    db.session.add(journey)
    db.session.commit()

    if coordinates:
        route_entry = Route(
            journey_id=journey.id,
            geometry_json=json.dumps(coordinates),
            recommended=True
        )
        db.session.add(route_entry)
        db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Journey initialized',
        'journey': journey.to_dict()
    }), 201

@journey_bp.route('/api/journeys/<int:journey_id>', methods=['GET'])
def get_journey(journey_id):
    journey = db.session.get(Journey, journey_id)
    if not journey:
        return jsonify({'error': 'Journey not found'}), 404
    
    routes = [r.to_dict() for r in journey.routes]
    data = journey.to_dict()
    data['routes'] = routes
    return jsonify({'journey': data}), 200

@journey_bp.route('/api/journeys/<int:journey_id>/location', methods=['POST'])
def update_location(journey_id):
    journey = db.session.get(Journey, journey_id)
    if not journey:
        return jsonify({'error': 'Journey not found'}), 404

    data = request.get_json() or {}
    lat = data.get('latitude')
    lon = data.get('longitude')
    force_deviation = data.get('force_deviation', False)

    if lat is None or lon is None:
        return jsonify({'error': 'Latitude and longitude are required'}), 400

    deviation_threshold = current_app.config.get('DEVIATION_THRESHOLD_METERS', 50.0)

    route = Route.query.filter_by(journey_id=journey.id).first()
    route_coords = route.get_geometry() if route else []

    if force_deviation:
        dist_to_route = 120.0
    else:
        dist_to_route = min_distance_to_route_meters(lat, lon, route_coords) if route_coords else 0.0

    is_deviated = dist_to_route > deviation_threshold
    nearest_haven_info = EmergencyService.get_nearest_safe_haven(lat, lon)

    if is_deviated:
        safety_status = 'RED'
        status_message = f'Route deviation detected ({int(dist_to_route)}m from planned corridor)'
        prompt_safety_check = True
    elif dist_to_route > 25.0:
        safety_status = 'YELLOW'
        status_message = 'Lower-confidence safety corridor / minor divergence'
        prompt_safety_check = False
    else:
        safety_status = 'GREEN'
        status_message = 'On planned safe route'
        prompt_safety_check = False

    return jsonify({
        'journey_id': journey.id,
        'current_location': {'latitude': lat, 'longitude': lon},
        'distance_to_route_meters': round(dist_to_route, 1),
        'deviation_threshold_meters': deviation_threshold,
        'is_deviated': is_deviated,
        'safety_status': safety_status,
        'status_message': status_message,
        'prompt_safety_check': prompt_safety_check,
        'nearest_haven': nearest_haven_info
    }), 200

@journey_bp.route('/api/journeys/<int:journey_id>/safety-check', methods=['POST'])
def submit_safety_check(journey_id):
    journey = db.session.get(Journey, journey_id)
    if not journey:
        return jsonify({'error': 'Journey not found'}), 404

    data = request.get_json() or {}
    is_safe = data.get('is_safe', True)
    lat = data.get('latitude', 12.9780)
    lon = data.get('longitude', 77.6010)

    if not is_safe:
        journey.status = 'EMERGENCY'
        db.session.commit()
        nearest_haven = EmergencyService.get_nearest_safe_haven(lat, lon)
        return jsonify({
            'success': True,
            'is_safe': False,
            'journey_status': 'EMERGENCY',
            'action_required': 'EMERGENCY_ASSISTANCE',
            'nearest_haven': nearest_haven,
            'emergency_options': [
                {'action': 'navigate_haven', 'label': 'Navigate to Nearest Safe Haven'},
                {'action': 'call_contact', 'label': 'Call Emergency Contact'},
                {'action': 'call_police', 'label': 'Call Police (100)'},
                {'action': 'call_ambulance', 'label': 'Call Ambulance (108)'},
                {'action': 'share_location', 'label': 'Share Live Location with Trusted Contacts'}
            ]
        }), 200
    else:
        journey.status = 'IN_PROGRESS'
        db.session.commit()
        return jsonify({
            'success': True,
            'is_safe': True,
            'journey_status': 'IN_PROGRESS',
            'message': 'Safety confirmed. Continuing journey tracking.'
        }), 200

@journey_bp.route('/api/journeys/<int:journey_id>/complete', methods=['POST'])
def complete_journey(journey_id):
    journey = db.session.get(Journey, journey_id)
    if not journey:
        return jsonify({'error': 'Journey not found'}), 404

    now_str = datetime.now(timezone.utc).strftime("%I:%M %p")
    journey.status = 'COMPLETED'
    journey.arrival_time = now_str
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Journey marked as completed',
        'journey': journey.to_dict()
    }), 200

@journey_bp.route('/api/journeys/history', methods=['GET'])
def get_journey_history():
    user_id = request.args.get('user_id', type=int)
    query = Journey.query
    if user_id:
        query = query.filter_by(user_id=user_id)

    journeys = query.order_by(Journey.created_at.desc()).all()
    if not journeys and current_app.config.get('DEMO_MODE', True):
        return jsonify({
            'success': True,
            'journeys': [
                {
                    'id': 101,
                    'origin': 'City College Campus',
                    'destination': 'Central Library',
                    'vehicle': 'personal_vehicle',
                    'departure_time': '02:15 PM',
                    'arrival_time': '02:37 PM',
                    'distance': 6.2,
                    'duration': 22,
                    'safety_score': 87,
                    'resilience_score': 92,
                    'max_time_to_haven': 108,
                    'status': 'COMPLETED',
                    'created_at': datetime.now(timezone.utc).isoformat()
                },
                {
                    'id': 100,
                    'origin': 'Downtown Tech Park',
                    'destination': 'Home (West End)',
                    'vehicle': 'cab',
                    'departure_time': '09:40 PM',
                    'arrival_time': '10:05 PM',
                    'distance': 8.4,
                    'duration': 25,
                    'safety_score': 84,
                    'resilience_score': 89,
                    'max_time_to_haven': 115,
                    'status': 'COMPLETED',
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
            ]
        }), 200

    return jsonify({
        'success': True,
        'journeys': [j.to_dict() for j in journeys]
    }), 200

@journey_bp.route('/api/journeys/<int:journey_id>', methods=['DELETE'])
def delete_journey(journey_id):
    journey = db.session.get(Journey, journey_id)
    if not journey:
        return jsonify({'error': 'Journey not found'}), 404

    db.session.delete(journey)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Journey history record deleted.'}), 200
