import datetime
from typing import Dict, Any, List, Optional
from backend.config import Config

class SafetyScoringEngine:
    """
    Modular Safety Scoring Engine.
    Evaluates multi-factor safety signals normalized to 0-100 scale:
    - Lighting coverage & street visibility
    - Incident-risk safety score (inversely proportional to verified incidents)
    - Foot traffic & pedestrian density
    - Proximity to emergency services (police, fire, ambulance hubs)
    - Time-of-day risk adaptation
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or Config.SAFETY_WEIGHTS.copy()
        # Ensure weights sum to 1.0
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            self.weights = {k: v / total_weight for k, v in self.weights.items()}

    def get_time_multiplier(self, departure_time_str: Optional[str] = None) -> float:
        """
        Calculate time-dependent risk factor.
        - Daytime (06:00 - 19:00): 1.0 (Full visibility, high natural surveillance)
        - Evening (19:00 - 22:30): 0.95 (Moderate foot traffic)
        - Night (22:30 - 05:59): 0.85 (Lower foot traffic, reliance on street lighting)
        """
        if not departure_time_str:
            hour = datetime.datetime.now().hour
        else:
            try:
                # Support "HH:MM" or "HH:MM AM/PM"
                time_str = departure_time_str.strip()
                if "AM" in time_str.upper() or "PM" in time_str.upper():
                    dt = datetime.datetime.strptime(time_str, "%I:%M %p")
                else:
                    dt = datetime.datetime.strptime(time_str.split()[0], "%H:%M")
                hour = dt.hour
            except Exception:
                hour = datetime.datetime.now().hour

        if 6 <= hour < 19:
            return 1.0
        elif 19 <= hour < 22:
            return 0.95
        elif 22 <= hour < 24 or 0 <= hour < 4:
            return 0.85
        else: # 4 to 6 AM
            return 0.90

    def calculate_score(
        self,
        lighting: Optional[float] = None,
        incidents: Optional[float] = None,
        foot_traffic: Optional[float] = None,
        emergency_services: Optional[float] = None,
        cctv_coverage: Optional[float] = None,
        departure_time: Optional[str] = None,
        safety_preference: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Calculates normalized composite safety score (0-100) across 5 core real-time safety factors:
        1. Streetlights & Illumination (lighting)
        2. Low Crime Rate & No Robbery (incidents)
        3. Crowded Area & Foot Traffic (foot_traffic)
        4. Nearby Safety Locations & Sanctuaries (emergency_services)
        5. CCTV Cameras & Surveillance (cctv_coverage)
        """
        confidence_flags = []
        
        # Normalize and fill defaults if missing
        norm_lighting = lighting if lighting is not None else 65.0
        if lighting is None:
            confidence_flags.append("Estimated baseline lighting used")

        norm_incidents = incidents if incidents is not None else 80.0
        if incidents is None:
            confidence_flags.append("Historical regional average crime/robbery rate applied")

        norm_foot_traffic = foot_traffic if foot_traffic is not None else 70.0
        if foot_traffic is None:
            confidence_flags.append("Estimated typical pedestrian volume used")

        norm_emergency = emergency_services if emergency_services is not None else 75.0
        if emergency_services is None:
            confidence_flags.append("Estimated emergency hub reachability applied")

        norm_cctv = cctv_coverage if cctv_coverage is not None else ((norm_lighting + norm_incidents) / 2.0)

        # Clamp all inputs to [0, 100]
        norm_lighting = max(0.0, min(100.0, float(norm_lighting)))
        norm_incidents = max(0.0, min(100.0, float(norm_incidents)))
        norm_foot_traffic = max(0.0, min(100.0, float(norm_foot_traffic)))
        norm_emergency = max(0.0, min(100.0, float(norm_emergency)))
        norm_cctv = max(0.0, min(100.0, float(norm_cctv)))

        # 5-Factor Weighted Score
        w_lighting = 0.22
        w_incidents = 0.22  # Low Crime & No Robbery
        w_foot = 0.20       # Crowded Area
        w_haven = 0.20      # Nearby Safety Locations
        w_cctv = 0.16       # CCTV Surveillance

        if safety_preference.lower() == "safest":
            w_lighting *= 1.2
            w_incidents *= 1.2
            w_haven *= 1.2

        total_w = w_lighting + w_incidents + w_foot + w_haven + w_cctv
        w_lighting /= total_w
        w_incidents /= total_w
        w_foot /= total_w
        w_haven /= total_w
        w_cctv /= total_w

        raw_score = (
            norm_lighting * w_lighting +
            norm_incidents * w_incidents +
            norm_foot_traffic * w_foot +
            norm_emergency * w_haven +
            norm_cctv * w_cctv
        )

        time_multiplier = self.get_time_multiplier(departure_time)
        final_score = int(round(raw_score * time_multiplier))
        final_score = max(1, min(99, final_score))

        confidence_level = "HIGH" if len(confidence_flags) == 0 else ("MEDIUM" if len(confidence_flags) <= 2 else "LOW")

        return {
            "safety_score": final_score,
            "lighting_score": int(round(norm_lighting)),
            "foot_traffic_score": int(round(norm_foot_traffic)),
            "incident_safety_score": int(round(norm_incidents)),
            "emergency_proximity_score": int(round(norm_emergency)),
            "cctv_coverage_score": int(round(norm_cctv)),
            "time_multiplier": round(time_multiplier, 2),
            "confidence_level": confidence_level,
            "confidence_notes": confidence_flags,
            "weights_used": {
                "streetlights": round(w_lighting, 2),
                "low_crime_rate": round(w_incidents, 2),
                "crowded_area": round(w_foot, 2),
                "nearby_safety_locations": round(w_haven, 2),
                "cctv_surveillance": round(w_cctv, 2)
            },
            "disclaimer": "Advisory risk estimate based on real-time environmental signals (streetlights, crowd density, crime reports, CCTV coverage, and safe havens)."
        }
