#!/usr/bin/env python3
"""Test V2.5.1 with H Pattern"""

import sys
sys.path.insert(0, '/home/user/webapp')

from shapely.geometry import Polygon
from app.professional_layout_engine import ProfessionalLayoutEngine
import time

boundary = Polygon([
    (0, 0), (70.4, 0), (70.4, 10), (60, 10),
    (60, 50.4), (10, 50.4), (10, 40), (0, 40), (0, 0)
])

print("=" * 80)
print("🧪 V2.5.1 TEST - H Pattern (Optimized)")
print("=" * 80)
print(f"Boundary: {boundary.area:.1f} m²\n")

engine = ProfessionalLayoutEngine(boundary)

cores = engine.place_cores(core_count=1, core_area=40.0)
print(f"✅ Core: {sum(c.area for c in cores):.1f} m²")

# Use H pattern (10% corridors, better than grid's 17%)
corridors = engine.create_visible_corridor_network(cores[0], corridor_width=2.5, pattern='H')
corridor_area = sum(c.area for c in corridors)
corridor_ratio = corridor_area / boundary.area * 100
print(f"✅ Corridors ({len(corridors)} segments): {corridor_area:.1f} m² ({corridor_ratio:.1f}%)")

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

start = time.time()
units = engine.layout_units_with_corridor_access(
    unit_constraints=unit_constraints,
    core=cores[0],
    corridors=corridors
)
elapsed = time.time() - start

units_area = sum(u['area'] for u in units)
core_area = sum(c.area for c in cores)
efficiency = units_area / boundary.area * 100
total_used = core_area + corridor_area + units_area
coverage = total_used / boundary.area * 100
wasted = boundary.area - total_used
wasted_pct = (wasted / boundary.area) * 100

print(f"✅ Units: {len(units)} placed in {elapsed:.1f}s\n")

from collections import Counter
type_counts = Counter([u['type'] for u in units])
print("📊 Distribution:")
for unit_type in ['Studio', '1BR', '2BR', '3BR']:
    count = type_counts.get(unit_type, 0)
    percentage = count / len(units) * 100 if units else 0
    print(f"  {unit_type}: {count} ({percentage:.1f}%)")

print(f"\n📈 Final Metrics:")
print(f"  Core:      {core_area:7.1f} m² ({core_area/boundary.area*100:5.1f}%)")
print(f"  Corridors: {corridor_area:7.1f} m² ({corridor_ratio:5.1f}%)")
print(f"  Units:     {units_area:7.1f} m² ({efficiency:5.1f}%)")
print(f"  {'─'*45}")
print(f"  TOTAL:     {total_used:7.1f} m² ({coverage:5.1f}%) ✅")
print(f"  WASTED:    {wasted:7.1f} m² ({wasted_pct:5.1f}%)")

print("\n" + "=" * 80)
print("✅ V2.5.1 SUCCESS CRITERIA:")
print("=" * 80)

criteria = {
    "Total coverage ≥95%": coverage >= 95,
    "Wasted <5%": wasted_pct < 5,
    "Units ≥45": len(units) >= 45,
    "Efficiency ≥80%": efficiency >= 80,
    "Corridors 8-12%": 8 <= corridor_ratio <= 12,
    "Time <30s": elapsed < 30
}

all_passed = True
for criterion, passed in criteria.items():
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {criterion}")
    if not passed:
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("🎉🎉🎉 V2.5.1 SUCCESS - 95%+ ACHIEVED! 🎉🎉🎉")
else:
    print(f"⚠️  Progress: {coverage:.1f}% coverage (target 95%)")
    print(f"    Gap: {max(0, 95-coverage):.1f}% remaining")
print("=" * 80)

