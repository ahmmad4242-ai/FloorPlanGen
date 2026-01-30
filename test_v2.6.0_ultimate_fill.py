"""
Test V2.6.0 - ULTIMATE FILL for 95%+ Coverage

Changes:
1. Grid Spacing: 0.5m → 0.15-0.25m (finer)
2. Wall Spacing: 0.15m → 0.05m (5cm realistic)
3. Excellent Threshold: 0.92 → 0.78 (more exploration)
4. Pass 1 max_attempts: 300 → 500
5. Pass 2 max_attempts: 500 → 800
6. Pass 3 max_attempts: 1500 → 2000
7. NEW Pass 4: Gap Filling with min_area_match=0.15, max_attempts=3000

TARGET: 95%+ Coverage
"""
import sys
sys.path.append('/home/user/webapp')
from shapely.geometry import Polygon
from app.professional_layout_engine import ProfessionalLayoutEngine
import time

print("=" * 80)
print("🎯 V2.6.0 - ULTIMATE FILL TEST (Target: 95%+ Coverage)")
print("=" * 80)

# Test boundary (same as before)
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
core = engine.place_cores(core_count=1, core_area=core_area)[0]
print(f"🏢 Core: {core.area:.1f} m² ({core.area/boundary.area*100:.1f}%)")

# Create corridor network (H pattern - best performer)
from app.corridor_patterns import CorridorPatternGenerator
corridor_gen = CorridorPatternGenerator(boundary, core, corridor_width=2.3)
corridors = corridor_gen.generate(pattern='H')
corridor_area = sum(c.area for c in corridors)
print(f"🛣️  Corridors ({len(corridors)} segments): {corridor_area:.1f} m² ({corridor_area/boundary.area*100:.1f}%)")

# Unit constraints
unit_constraints = {
    "generation_strategy": "fill_available",
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
    "total_units": {"min": 15, "max": 50}
}

# Generate layout
print(f"\n🏗️  Generating layout with V2.6.0 ULTIMATE FILL...")
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
print("📊 V2.6.0 RESULTS")
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
    pct = count / len(units) * 100
    print(f"  • {ut}: {count} ({pct:.1f}%)")

print(f"\n⏱️  Generation time: {elapsed:.1f}s")

print(f"\n" + "=" * 80)
print("✅ SUCCESS CRITERIA - V2.6.0 (95%+ Coverage Target)")
print("=" * 80)

criteria = [
    ("Total Coverage ≥95%", coverage >= 95, f"{coverage:.1f}%"),
    ("Wasted <5%", wasted_pct < 5, f"{wasted_pct:.1f}%"),
    ("Units ≥45", len(units) >= 45, f"{len(units)} units"),
    ("Efficiency ≥80%", efficiency >= 80, f"{efficiency:.1f}%"),
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
    print("🎉 V2.6.0 SUCCESS! All criteria MET! Ready for production!")
else:
    print(f"⚠️  V2.6.0 PARTIAL: {coverage:.1f}% coverage (Gap: {95-coverage:.1f}%)")
    
    # Detailed analysis
    available_after_corridors = boundary.area - core.area - corridor_area
    units_vs_available = units_area / available_after_corridors * 100
    print(f"\n🔍 Detailed Analysis:")
    print(f"  • Available after corridors: {available_after_corridors:.1f} m²")
    print(f"  • Units vs available: {units_vs_available:.1f}%")
    print(f"  • Lost space: {available_after_corridors - units_area:.1f} m²")
print("=" * 80)
