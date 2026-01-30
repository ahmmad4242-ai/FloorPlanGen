#!/usr/bin/env python3
"""Test V2.5.0 - Grid Pattern + Multi-Core Support"""

import sys
sys.path.insert(0, '/home/user/webapp')

from shapely.geometry import Polygon
from app.professional_layout_engine import ProfessionalLayoutEngine

# Real boundary from user (3024 m²)
boundary = Polygon([
    (0, 0), (70.4, 0), (70.4, 10), (60, 10),
    (60, 50.4), (10, 50.4), (10, 40), (0, 40), (0, 0)
])

print("=" * 80)
print("🧪 V2.5.0 TEST - Grid Pattern + Multi-Core")
print("=" * 80)
print(f"\nBoundary: {boundary.area:.1f} m²")

# Initialize engine
engine = ProfessionalLayoutEngine(boundary)

# Test 1: Single core + Grid pattern
print("\n" + "=" * 80)
print("TEST 1: Single Core + Grid Pattern")
print("=" * 80)

cores = engine.place_cores(core_count=1, core_area=40.0)
print(f"Cores: {len(cores)} × {sum(c.area for c in cores):.1f} m²")

corridors = engine.create_visible_corridor_network(cores[0], corridor_width=2.5, pattern='grid')
print(f"Corridors: {len(corridors)} segments")

corridor_area = sum(c.area for c in corridors)
corridor_ratio = corridor_area / boundary.area * 100
print(f"Corridor area: {corridor_area:.1f} m² ({corridor_ratio:.1f}%)")

# Unit constraints
unit_constraints = {
    "generation_strategy": "fill_available",
    "units": [
        {"type": "Studio", "percentage": 20, "priority": 2,
         "area": {"min": 25, "max": 35, "target": 30}},
        {"type": "1BR", "percentage": 40, "priority": 1,
         "area": {"min": 45, "max": 65, "target": 55}},
        {"type": "2BR", "percentage": 30, "priority": 1,
         "area": {"min": 65, "max": 85, "target": 75}},
        {"type": "3BR", "percentage": 10, "priority": 3,
         "area": {"min": 85, "max": 110, "target": 97.5}}
    ],
    "total_units": {"min": 15, "max": 50},
    "distribution_strategy": "balanced"
}

units = engine.layout_units_with_corridor_access(
    unit_constraints=unit_constraints,
    core=cores[0],
    corridors=corridors
)

units_area = sum(u['area'] for u in units)
efficiency = units_area / boundary.area * 100
total_used = (sum(c.area for c in cores) + corridor_area + units_area)
coverage = total_used / boundary.area * 100

print(f"\nResults:")
print(f"  Units: {len(units)}")
print(f"  Units area: {units_area:.1f} m²")
print(f"  Efficiency: {efficiency:.1f}%")
print(f"  Total coverage: {coverage:.1f}%")
print(f"  Wasted: {boundary.area - total_used:.1f} m² ({100-coverage:.1f}%)")

# Test 2: Dual core + Grid pattern
print("\n" + "=" * 80)
print("TEST 2: Dual Core + Grid Pattern")
print("=" * 80)

engine2 = ProfessionalLayoutEngine(boundary)
cores2 = engine2.place_cores(core_count=2, core_area=40.0)
print(f"Cores: {len(cores2)} × {sum(c.area for c in cores2):.1f} m²")

# For multi-core, use first core for corridor generation
corridors2 = engine2.create_visible_corridor_network(cores2[0], corridor_width=2.5, pattern='grid')
print(f"Corridors: {len(corridors2)} segments")

corridor_area2 = sum(c.area for c in corridors2)
corridor_ratio2 = corridor_area2 / boundary.area * 100
print(f"Corridor area: {corridor_area2:.1f} m² ({corridor_ratio2:.1f}%)")

print("\n" + "=" * 80)
print("✅ SUCCESS CRITERIA:")
print("=" * 80)

criteria = {
    "Corridors ≥6": len(corridors) >= 6,
    "Corridor coverage 8-15%": 8 <= corridor_ratio <= 15,
    "Units ≥40": len(units) >= 40,
    "Efficiency ≥80%": efficiency >= 80,
    "Total coverage ≥95%": coverage >= 95,
    "Wasted <5%": (100 - coverage) < 5
}

all_passed = True
for criterion, passed in criteria.items():
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {criterion}")
    if not passed:
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("🎉 V2.5.0 GRID PATTERN SUCCESS!")
else:
    print("⚠️  Target not met - analyzing...")
print("=" * 80)

