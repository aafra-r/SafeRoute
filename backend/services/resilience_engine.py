from typing import List, Dict, Any, Optional
from backend.config import Config
from backend.utils.geo_helper import sample_polyline_points, haversine_distance_meters

class SafetyResilienceEngine:
    """
    Core Safety Resilience Engine.
    At every point along a route, determines the estimated time required
    for a user to reach the nearest verified safe haven.
    """

    def __init__(self, default_threshold_seconds: Optional[int] = None, travel_speed_mps: float = 1.3):
        # Default 120 seconds / 2 minutes
        self.threshold_seconds = default_threshold_seconds or Config.RESILIENCE_THRESHOLD_SECONDS
        # Average emergency pedestrian speed = 1.3 m/s (~4.7 km/h)
        self.travel_speed_mps = travel_speed_mps

    def analyze_route_resilience(
        self,
        route_coordinates: List[Dict[str, float]],
        safe_havens: List[Dict[str, Any]],
        threshold_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyzes route resilience profile across sampled points.
        Returns resilience_score, max_time_to_haven, avg_time_to_haven,
        percentage within threshold, and pass/warning status.
        """
        threshold = threshold_seconds or self.threshold_seconds

        if not route_coordinates:
            return {
                "resilience_score": 0,
                "max_time_to_haven": 999,
                "avg_time_to_haven": 999,
                "min_time_to_haven": 999,
                "havens_count": 0,
                "threshold_seconds": threshold,
                "meets_threshold": False,
                "resilience_status": "WARNING",
                "percent_within_threshold": 0.0,
                "time_to_haven_profile": [],
                "disclaimer": "Threshold is a design metric, not an emergency response guarantee."
            }

        if not safe_havens:
            return {
                "resilience_score": 30,
                "max_time_to_haven": 600,
                "avg_time_to_haven": 450,
                "min_time_to_haven": 300,
                "havens_count": 0,
                "threshold_seconds": threshold,
                "meets_threshold": False,
                "resilience_status": "WARNING",
                "percent_within_threshold": 0.0,
                "time_to_haven_profile": [],
                "notes": "No verified safe havens detected along this corridor.",
                "disclaimer": "Threshold is a design metric, not an emergency response guarantee."
            }

        # 1. Sample route points at ~80m intervals
        sampled_points = sample_polyline_points(route_coordinates, sample_interval_meters=80.0)
        
        time_profile = []
        havens_within_corridor = set()

        for pt in sampled_points:
            min_dist_meters = float('inf')
            closest_haven_id = None
            closest_haven_name = None

            for haven in safe_havens:
                dist = haversine_distance_meters(
                    pt['latitude'], pt['longitude'],
                    haven['latitude'], haven['longitude']
                )
                if dist < min_dist_meters:
                    min_dist_meters = dist
                    closest_haven_id = haven.get('id')
                    closest_haven_name = haven.get('name')

            # Calculate time in seconds: distance / speed
            time_to_haven_sec = int(round(min_dist_meters / self.travel_speed_mps))
            if min_dist_meters <= 1200: # Within 1.2km corridor
                havens_within_corridor.add(closest_haven_id)

            time_profile.append({
                "latitude": pt['latitude'],
                "longitude": pt['longitude'],
                "time_to_haven_seconds": time_to_haven_sec,
                "nearest_haven_id": closest_haven_id,
                "nearest_haven_name": closest_haven_name,
                "within_threshold": time_to_haven_sec <= threshold
            })

        times = [p["time_to_haven_seconds"] for p in time_profile]
        max_time = max(times) if times else 0
        min_time = min(times) if times else 0
        avg_time = int(round(sum(times) / len(times))) if times else 0

        points_within_threshold = sum(1 for p in time_profile if p["within_threshold"])
        percent_within = round((points_within_threshold / len(time_profile)) * 100.0, 1) if time_profile else 0.0

        # Resilience score calculation (0 to 100)
        # 100 if max_time <= threshold, decreases gracefully as max_time exceeds threshold
        if max_time <= threshold:
            # High resilience
            resilience_score = int(round(90 + (10 * (1 - max_time / threshold))))
        else:
            # Scaled down based on threshold overshoot and percent covered
            penalty = min(60, int(((max_time - threshold) / threshold) * 40))
            resilience_score = max(20, int(round((percent_within * 0.7) + (30 - penalty * 0.5))))

        meets_threshold = max_time <= threshold
        resilience_status = "PASS" if meets_threshold else "WARNING"

        return {
            "resilience_score": resilience_score,
            "max_time_to_haven": max_time,
            "avg_time_to_haven": avg_time,
            "min_time_to_haven": min_time,
            "havens_count": len(havens_within_corridor),
            "threshold_seconds": threshold,
            "meets_threshold": meets_threshold,
            "resilience_status": resilience_status,
            "percent_within_threshold": percent_within,
            "time_to_haven_profile": time_profile[::max(1, len(time_profile) // 10)], # Subsample for compact API response
            "disclaimer": "Estimated time to nearest safe haven is an advisory threshold metric, not an emergency guarantee."
        }
