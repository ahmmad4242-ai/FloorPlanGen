#!/usr/bin/env python3
"""Test V2.4.3 CRITICAL FIX for Pass 2 & Pass 3 constraints"""

import sys
import os
sys.path.insert(0, '/home/user/webapp')

from shapely.geometry import Polygon
from app.professional_layout_engine import ProfessionalLayoutEngine

# Real boundary from user (3121.79 m²)
boundary = Polygon([
    (0, 0), (70.4, 0), (70.4, 10), (60, 10),
    (60, 50.4), (10, 50.4), (10, 40), (0, 40), (0, 0)
])

print("=" * 80)
print("🧪 V2.4.3 CRITICAL FIX TEST - Multi-Pass Placement")
print("=" * 80)
print(f"\nBoundary: {boundary.area:.1f} m²")

# Initialize engine (obstacles default to None)
engine = ProfessionalLayoutEngine(boundary)

# Place core
core = engine.place_core(core_area=40.0, preferred_location='center')
print(f"Core: {core.area:.1f} m² at center")

# Create corridors
corridors = engine.create_visible_corridor_network(core, corridor_width=2.5, pattern='auto')
print(f"Corridors: {len(corridors)} segments")

# Unit constraints (V2)
unit_constraints = {
    "generation_strategy": "fill_available",
    "units": [
        {
            "type": "Studio",
            "percentage": 20,
            "priority": 2,
            "area": {"min": 25, "max": 35, "target": 30}
        },
        {
            "type": "1BR",
            "percentage": 40,
            "priority": 1,
            "area": {"min": 45, "max": 65, "target": 55}
        },
        {
            "type": "2BR",
            "percentage": 30,
            "priority": 1,
            "area": {"min": 65, "max": 85, "target": 75}
        },
        {
            "type": "3BR",
            "percentage": 10,
            "priority": 3,
            "area": {"min": 85, "max": 110, "target": 97.5}
        }
    ],
    "total_units": {"min": 15, "max": 50},
    "distribution_strategy": "balanced"
}

# Layout units
import time
start = time.time()
units = engine.layout_units_with_corridor_access(
    unit_constraints=unit_constraints,
    core=core,
    corridors=corridors
)
elapsed = time.time() - start

print(f"\n{'=' * 80}")
print("📊 PLACEMENT RESULTS:")
print(f"{'=' * 80}")
print(f"Total units placed: {len(units)} in {elapsed:.1f}s")

# Count by type
from collections import Counter
type_counts = Counter([u['type'] for u in units])
print(f"\nDistribution:")
for unit_type in ['Studio', '1BR', '2BR', '3BR']:
    count = type_counts.get(unit_type, 0)
    percentage = count / len(units) * 100 if units else 0
    print(f"  {unit_type}: {count} ({percentage:.1f}%)")

# Calculate metrics
total_units_area = sum([u['area'] for u in units])
efficiency = total_units_area / boundary.area * 100

print(f"\nMetrics:")
print(f"  Units area: {total_units_area:.1f} m²")
print(f"  Efficiency: {efficiency:.1f}%")
print(f"  Core: {core.area:.1f} m²")

print(f"\n{'=' * 80}")
print("✅ SUCCESS CRITERIA:")
print(f"{'=' * 80}")

criteria = {
    "Units placed ≥30": len(units) >= 30,
    "Efficiency ≥50%": efficiency >= 50,
    "Time <30s": elapsed < 30,
    "Studio 15-25%": 15 <= (type_counts.get('Studio', 0) / len(units) * 100 if units else 0) <= 25,
    "1BR 35-45%": 35 <= (type_counts.get('1BR', 0) / len(units) * 100 if units else 0) <= 45,
}

all_passed = True
for criterion, passed in criteria.items():
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {criterion}")
    if not passed:
        all_passed = False

print(f"\n{'=' * 80}")
if all_passed:
    print("🎉 V2.4.3 FIX SUCCESSFUL!")
else:
    print("⚠️  Some criteria not met - may need further tuning")
print(f"{'=' * 80}")

