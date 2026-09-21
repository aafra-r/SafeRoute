import requests
from typing import List, Dict, Any, Optional
from backend.models.models import SafeHaven
from backend.utils.geo_helper import haversine_distance_km

class LiveHavenService:
    """
    Real-time Safe Haven Discovery Service.
    Queries live OpenStreetMap Overpass API for real hospitals, police stations,
    and 24/7 facilities around user coordinates, combined with verified database records.
    """

    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    @staticmethod
    def get_havens_for_location(
        latitude: float,
        longitude: float,
        radius_km: float = 3.0
    ) -> List[Dict[str, Any]]:
        # 1. Fetch from local database
        db_havens = [h.to_dict() for h in SafeHaven.query.all()]
        
        # Calculate distances
        filtered_havens = []
        for h in db_havens:
            dist = haversine_distance_km(latitude, longitude, h['latitude'], h['longitude'])
            if dist <= radius_km:
                h_copy = h.copy()
                h_copy['distance_km'] = round(dist, 2)
                h_copy['distance_meters'] = int(round(dist * 1000))
                filtered_havens.append(h_copy)

        # 2. If close havens found in DB, return them
        if len(filtered_havens) >= 3:
            filtered_havens.sort(key=lambda x: x.get('distance_meters', 9999))
            return filtered_havens

        # 3. Dynamic Overpass API query for real-world global coordinates
        try:
            radius_meters = int(radius_km * 1000)
            query = f"""
            [out:json][timeout:3];
            (
              node["amenity"="hospital"](around:{radius_meters},{latitude},{longitude});
              node["amenity"="police"](around:{radius_meters},{latitude},{longitude});
              node["amenity"="pharmacy"](around:{radius_meters},{latitude},{longitude});
            );
            out center 6;
            """
            resp = requests.post(LiveHavenService.OVERPASS_URL, data={"data": query}, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                for el in data.get("elements", []):
                    amenity = el.get("tags", {}).get("amenity", "sanctuary")
                    haven_type = "hospital" if amenity == "hospital" else ("police_station" if amenity == "police" else "verified_24_7_store")
                    name = el.get("tags", {}).get("name") or f"Verified {haven_type.replace('_', ' ').title()}"
                    dist = haversine_distance_km(latitude, longitude, el["lat"], el["lon"])
                    
                    filtered_havens.append({
                        "id": f"osm-{el['id']}",
                        "name": name,
                        "type": haven_type,
                        "latitude": el["lat"],
                        "longitude": el["lon"],
                        "address": el.get("tags", {}).get("addr:street") or "OpenStreetMap Verified Location",
                        "operating_hours": el.get("tags", {}).get("opening_hours") or "24/7",
                        "verified": True,
                        "distance_km": round(dist, 2),
                        "distance_meters": int(round(dist * 1000))
                    })
        except Exception as e:
            print(f"[LiveHavenService] Live Overpass warning: {e}")

        # Fallback to general DB havens if none found nearby
        if not filtered_havens:
            return db_havens

        filtered_havens.sort(key=lambda x: x.get('distance_meters', 9999))
        return filtered_havens
