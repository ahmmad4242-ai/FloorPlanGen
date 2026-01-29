#!/usr/bin/env python3
"""
Test Generator Service Directly
"""
import requests
import json

GENERATOR_URL = "https://floorplangen-generator.onrender.com"

# Test data
test_request = {
    "project_id": "test-proj-123",
    "constraints": {
        "generation_strategy": "fill_available",
        "units": [
            {"type": "Studio", "percentage": 20, "min_area": 25, "max_area": 35, "priority": 1},
            {"type": "1BR", "percentage": 40, "min_area": 45, "max_area": 65, "priority": 2},
            {"type": "2BR", "percentage": 30, "min_area": 65, "max_area": 85, "priority": 3},
            {"type": "3BR", "percentage": 10, "min_area": 85, "max_area": 110, "priority": 4}
        ],
        "core": {"area_m2": 40},
        "circulation": {"corridor_width_m": 2.2}
    },
    "variant_count": 1,
    "dxf_url": None,
    "boundary_layer": "BOUNDARY"
}

print("Testing Generator Service directly...")
print(f"URL: {GENERATOR_URL}/generate")
print(f"Request: {json.dumps(test_request, indent=2)}")
print("\n" + "=" * 60)

try:
    response = requests.post(
        f"{GENERATOR_URL}/generate",
        json=test_request,
        timeout=120
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("\n✅ Generator is working!")
    else:
        print(f"\n❌ Generator returned {response.status_code}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
