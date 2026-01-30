"""
🚀 V3.0 Row-Based Layout - Comprehensive Test
Target: 95%+ Coverage

Revolutionary approach:
- No region.difference() fragmentation
- Units arranged in rows (like parking)
- Expected: 50-55 units, 95%+ coverage
"""
import sys
sys.path.append('/home/user/webapp')
from shapely.geometry import Polygon
from app.professional_layout_engine import ProfessionalLayoutEngine
from app.corridor_patterns import CorridorPatternGenerator
import time

print("=" * 80)
print("🚀 V3.0 ROW-BASED LAYOUT TEST (Target: 95%+ Coverage)")
print("=" * 80)

# Test boundary (L-shaped)
boundary_coords = [
    (0, 0), (70.4, 0), (70.4, 10), (60, 10),
    (60, 50.4), (10, 50.4), (10, 40), (0, 40)
]
boundary = Polygon(boundary_coords)

print(f"\n📐 Boundary: {boundary.area:.1f} m²")

# Initialize engine
engine = ProfessionalLayoutEngine(boundary, [])

# Place core
core_area = 40.0
cores = engine.place_cores(core_count=1, core_area=core_area)
core = cores[0] if cores else None
print(f"🏢 Core: {core.area:.1f} m² ({core.area/boundary.area*100:.1f}%)")

# Create corridor network (H pattern - best for row-based)
corridor_gen = CorridorPatternGenerator(boundary, core, corridor_width=2.3)
corridors = corridor_gen.generate(pattern='H')
corridor_area = sum(c.area for c in corridors)
print(f"🛣️  Corridors ({len(corridors)} segments): {corridor_area:.1f} m² ({corridor_area/boundary.area*100:.1f}%)")

# Unit constraints - V3.0 enabled!
unit_constraints = {
    "generation_strategy": "fill_available",
    "use_v3_row_based": True,  # ✅ ENABLE V3.0!
    "units": [
        {"type": "Studio", "percentage": 20, "priority": 1, 
         "area": {"min": 25, "target": 30, "max": 35}},
        {"type": "1BR", "percentage": 40, "priority": 1,
         "area": {"min": 45, "target": 55, "max": 65}},
        {"type": "2BR", "percentage": 30, "priority": 1,
         "area": {"min": 65, "target": 75, "max": 85}},
        {"type": "3BR", "percentage": 10, "priority": 1,
         "area": {"min": 85, "target": 97.5, "max": 110}}
    ],
    "total_units": {"min": 15, "max": 60}  # Allow more units!
}

# Generate layout with V3.0
print(f"\n🏗️  Generating layout with V3.0 ROW-BASED ALGORITHM...")
start_time = time.time()
units = engine.layout_units_with_corridor_access(core, corridors, unit_constraints)
elapsed = time.time() - start_time

# Calculate metrics
units_area = sum(u['area'] for u in units)
total_used = core.area + corridor_area + units_area
coverage = total_used / boundary.area * 100
wasted = boundary.area - total_used
wasted_pct = wasted / boundary.area * 100
efficiency = units_area / boundary.area * 100

print(f"\n" + "=" * 80)
print("📊 V3.0 ROW-BASED LAYOUT RESULTS")
print("=" * 80)

print(f"\n📦 Space Allocation:")
print(f"  • Boundary: {boundary.area:.1f} m² (100%)")
print(f"  • Core: {core.area:.1f} m² ({core.area/boundary.area*100:.1f}%)")
print(f"  • Corridors: {corridor_area:.1f} m² ({corridor_area/boundary.area*100:.1f}%)")
print(f"  • Units: {units_area:.1f} m² ({efficiency:.1f}%)")
print(f"  • ━━━━━━━━━━━━━━━━━━━━━━")
print(f"  • TOTAL USED: {total_used:.1f} m² ({coverage:.1f}%)")
print(f"  • WASTED: {wasted:.1f} m² ({wasted_pct:.1f}%)")

print(f"\n🏘️  Units: {len(units)} total")
units_by_type = {}
for u in units:
    ut = u['type']
    units_by_type[ut] = units_by_type.get(ut, 0) + 1

for ut, count in sorted(units_by_type.items()):
    pct = count / len(units) * 100 if units else 0
    print(f"  • {ut}: {count} ({pct:.1f}%)")

print(f"\n⏱️  Generation time: {elapsed:.1f}s")

print(f"\n" + "=" * 80)
print("✅ SUCCESS CRITERIA - V3.0 (95%+ Coverage Target)")
print("=" * 80)

criteria = [
    ("Total Coverage ≥95%", coverage >= 95, f"{coverage:.1f}%"),
    ("Wasted <5%", wasted_pct < 5, f"{wasted_pct:.1f}%"),
    ("Units ≥45", len(units) >= 45, f"{len(units)} units"),
    ("Efficiency ≥82%", efficiency >= 82, f"{efficiency:.1f}%"),
    ("Corridors 8-12%", 8 <= corridor_area/boundary.area*100 <= 12, f"{corridor_area/boundary.area*100:.1f}%"),
    ("Time <30s", elapsed < 30, f"{elapsed:.1f}s")
]

all_pass = True
for name, passed, value in criteria:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name} → {value}")
    if not passed:
        all_pass = False

print(f"\n" + "=" * 80)
if all_pass:
    print("🎉🎉🎉 V3.0 SUCCESS! ALL CRITERIA MET! 🎉🎉🎉")
    print("95%+ coverage achieved with row-based layout!")
else:
    # Comparison with V2.x
    print(f"⚠️  V3.0 RESULT: {coverage:.1f}% coverage")
    print(f"\n📈 Comparison:")
    print(f"  V2.5.1 (Region-Based):  66-77% coverage, 33-38 units")
    print(f"  V3.0   (Row-Based):     {coverage:.1f}% coverage, {len(units)} units")
    
    improvement = coverage - 66.5  # V2.5.1 baseline
    print(f"  Improvement: +{improvement:.1f}% coverage")
    
    if coverage >= 85:
        print(f"\n✅ Significant improvement over V2.x!")
    elif coverage >= 75:
        print(f"\n⚠️  Moderate improvement, needs refinement")
    else:
        print(f"\n❌ Did not improve over V2.x baseline")

print("=" * 80)
