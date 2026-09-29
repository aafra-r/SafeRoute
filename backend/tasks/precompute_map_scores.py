"""
CLI Script to precompute and cache safety map scores for all configured coverage areas.
Usage:
    python -m backend.tasks.precompute_map_scores
"""

import sys
import time
import requests
from backend.config.safety_map_config import COVERAGE_AREAS

BASE_URL = "http://127.0.0.1:5000"

def precompute_all_areas():
    print("==================================================")
    print("🚀 Precomputing Safety Map Scores for All Areas...")
    print("==================================================")

    for area in COVERAGE_AREAS:
        name = area["name"]
        bbox = area["bbox"]
        bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
        print(f"📍 Scoring area: {name} (bbox: {bbox_str})...")

        for mode in ['day', 'night']:
            url = f"{BASE_URL}/api/safety-map/segments?bbox={bbox_str}&time={mode}"
            try:
                start_time = time.time()
                resp = requests.get(url, timeout=15)
                elapsed = round(time.time() - start_time, 2)
                if resp.status_code == 200:
                    data = resp.json()
                    count = len(data.get("features", []))
                    print(f"   [SUCCESS] Mode: {mode.upper()} | Segments: {count} | Time: {elapsed}s")
                else:
                    print(f"   [FAIL] Mode: {mode.upper()} | Status: {resp.status_code}")
            except Exception as e:
                print(f"   [ERROR] Could not connect to backend server: {e}")

    print("==================================================")
    print("✅ Precomputation complete!")
    print("==================================================")

if __name__ == "__main__":
    precompute_all_areas()
