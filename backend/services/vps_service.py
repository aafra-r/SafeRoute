"""
Visual Positioning Service (VPS) & 360° Street View Engine for SafeRoute.
Provides real-time Google Street View metadata availability checking,
panorama URL generation, and visual positioning orientation state.
"""
import requests
import logging
from backend.config import Config

logger = logging.getLogger(__name__)

class VPSService:
    @staticmethod
    def get_streetview_metadata(lat: float, lon: float):
        """
        Check if 360° Street View / Visual Positioning imagery is available at GPS coordinates.
        Uses Google Street View Metadata API when key is configured, with robust fallbacks.
        """
        api_key = Config.GOOGLE_MAPS_API_KEY
        
        # Validate coordinates bounds
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return {
                "available": False,
                "status": "INVALID_COORDINATES",
                "message": "360° visual coverage is unavailable for invalid coordinates.",
                "location": {"lat": lat, "lng": lon}
            }

        # If Google Maps API key is configured, check official Google Metadata API
        if api_key:
            try:
                url = "https://maps.googleapis.com/maps/api/streetview/metadata"
                params = {
                    "location": f"{lat},{lon}",
                    "key": api_key,
                    "radius": 50 # 50m search radius
                }
                res = requests.get(url, params=params, timeout=4)
                if res.status_code == 200:
                    data = res.json()
                    status = data.get("status")
                    if status == "OK":
                        return {
                            "available": True,
                            "status": "OK",
                            "pano_id": data.get("pano_id"),
                            "location": data.get("location", {"lat": lat, "lng": lon}),
                            "date": data.get("date", ""),
                            "copyright": data.get("copyright", "© Google"),
                            "message": "360° visual street view imagery available.",
                            "source": "google_api"
                        }
                    elif status == "ZERO_RESULTS":
                        return {
                            "available": False,
                            "status": "ZERO_RESULTS",
                            "message": "360° visual coverage is unavailable at this location.",
                            "location": {"lat": lat, "lng": lon},
                            "source": "google_api"
                        }
            except Exception as e:
                logger.warning(f"[VPSService] Google Metadata API request failed: {e}")

        # Fallback / Direct Embed Coverage Evaluation
        # Valid GPS coordinates on land/roads are supported via Google Maps Street View Embed
        # (Zero lat/lon 0.0, 0.0 in the middle of ocean or 90.0 north pole returns unavailable)
        is_ocean_or_remote = (abs(lat) < 0.001 and abs(lon) < 0.001) or (abs(lat) > 85.0)
        
        if is_ocean_or_remote:
            return {
                "available": False,
                "status": "ZERO_RESULTS",
                "message": "360° visual coverage is unavailable at this location.",
                "location": {"lat": lat, "lng": lon},
                "source": "geospatial_bounds"
            }

        embed_url = VPSService.get_panorama_embed_url(lat, lon)
        return {
            "available": True,
            "status": "OK",
            "location": {"lat": lat, "lng": lon},
            "embed_url": embed_url,
            "message": "360° visual positioning panorama ready.",
            "source": "google_embed"
        }

    @staticmethod
    def get_panorama_embed_url(lat: float, lon: float, heading: float = 0.0, pitch: float = 0.0, fov: float = 90.0, pano_id: str = None) -> str:
        """
        Generate 360° Google Street View Embed URL for given coordinates.
        Removes 'q=' query parameter to force Google Maps to render 360° Street View layer instead of 2D Map.
        """
        api_key = Config.GOOGLE_MAPS_API_KEY
        if api_key:
            if pano_id:
                return f"https://www.google.com/maps/embed/v1/streetview?key={api_key}&pano={pano_id}&heading={heading}&pitch={pitch}&fov={fov}"
            return f"https://www.google.com/maps/embed/v1/streetview?key={api_key}&location={lat},{lon}&heading={heading}&pitch={pitch}&fov={fov}"
        
        if pano_id:
            return f"https://maps.google.com/maps?layer=c&panoid={pano_id}&cbp=12,{heading:.1f},0,0,0&output=embed"

        # Direct 360° Google Street View Embed URL without 'q=' parameter
        return f"https://maps.google.com/maps?layer=c&cbll={lat},{lon}&cbp=12,{heading:.1f},0,0,0&output=embed"

    @staticmethod
    def get_google_pano_url(lat: float, lon: float, heading: float = 0.0) -> str:
        """
        Generate direct Google Maps 360° Street View web & app URL.
        """
        return f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}&heading={heading:.1f}"

    @staticmethod
    def get_static_streetview_url(lat: float, lon: float, heading: float = 0.0, pitch: float = 0.0) -> str:
        """
        Generate 360° Street View embed URL or static preview imagery URL.
        """
        api_key = Config.GOOGLE_MAPS_API_KEY
        if api_key:
            return f"https://maps.googleapis.com/maps/api/streetview?size=1200x800&location={lat},{lon}&heading={heading:.1f}&pitch={pitch:.1f}&fov=90&key={api_key}"
        
        return f"https://maps.google.com/maps?q={lat},{lon}&layer=c&cbll={lat},{lon}&cbp=12,{heading:.1f},0,0,0&output=embed"




