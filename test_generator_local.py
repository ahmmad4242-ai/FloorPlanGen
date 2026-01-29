#!/usr/bin/env python3
"""Test Generator locally to verify it works"""

import sys
sys.path.insert(0, '/home/user/webapp/generator-service')

from app.main import generate_single_variant
from shapely.geometry import box
import json

# Simple test boundary
boundary = box(0, 0, 50, 30)
obstacles = []
fixed_elements = {}

# Test constraints with unit_types
constraints = {
    "units": [
        {"type": "Studio", "count": 5, "min_area": 25, "max_area": 35},
        {"type": "1BR", "count": 10, "min_area": 45, "max_area": 65},
        {"type": "2BR", "count": 8, "min_area": 65, "max_area": 85}
    ],
    "core": {
        "area_m2": {"target": 40, "min": 25, "max": 60}
    },
    "circulation": {
        "corridor_width_m": {"target": 2.2, "min": 1.8, "max": 2.5},
        "layout_type": "double_loaded"
    },
    "architectural_constraints": {
        "units": {
            "unit_types": [
                {"type": "Studio", "count": 5, "min_area": 25, "max_area": 35},
                {"type": "1BR", "count": 10, "min_area": 45, "max_area": 65},
                {"type": "2BR", "count": 8, "min_area": 65, "max_area": 85}
            ]
        }
    }
}

print("Testing Generator with NEW ArchitecturalLayoutEngine...")
print(f"Expected units: 23 (5 Studio + 10 1BR + 8 2BR)")
print()

result = generate_single_variant(
    project_id="test-local",
    variant_number=1,
    boundary=boundary,
    obstacles=obstacles,
    fixed_elements=fixed_elements,
    constraints=constraints
)

metadata = result["metadata"]
print(f"Results:")
print(f"  Units Count: {metadata['units_count']} / 23")
print(f"  Corridor Ratio: {metadata['corridor_ratio']*100:.1f}%")
print(f"  Efficiency: {metadata['efficiency']*100:.1f}%")
print(f"  Units Area: {metadata['units_area']:.2f} m²")

if metadata['units_count'] > 0:
    print(f"\n✅ SUCCESS! Generator is working with new engine!")
else:
    print(f"\n❌ FAILED! No units generated!")
