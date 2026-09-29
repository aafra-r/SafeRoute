"""
Configurable Coverage Area & Precomputation Settings for Safety Map Mode.
"""

COVERAGE_AREAS = [
    {
        "name": "Tiruchirappalli (Trichy) Central",
        "bbox": [10.74, 78.62, 10.86, 78.80],
        "default": True
    },
    {
        "name": "Trichy Campus Zone (Banyan & University)",
        "bbox": [10.78, 78.69, 10.80, 78.72],
        "default": False
    },
    {
        "name": "Chennai City Core",
        "bbox": [13.00, 80.20, 13.12, 80.30],
        "default": False
    }
]

PRECOMPUTE_INTERVAL_SEC = 600
DEFAULT_VEHICLE_MODE = "walking"
