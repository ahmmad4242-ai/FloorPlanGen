"""Test V3.1 Simplified Row-Based Layout"""
import sys
sys.path.insert(0, '/home/user/webapp')

from shapely.geometry import box
from app.corridor_patterns import CorridorPatternGenerator
from app.row_based_layout_v3_1 import RowBasedLayoutV31
import time

print("=" * 70)
print("V3.1 SIMPLIFIED ROW-BASED LAYOUT TEST")
print("=" * 70)

# 1. Create test boundary (63m × 48m = 3024 m²)
boundary = box(0, 0, 63, 48)
print(f"✅ Boundary: {boundary.area:.2f} m²")

# 2. Create core (8m × 5m = 40 m²)
core = box(27.5, 21.5, 35.5, 26.5)
print(f"✅ Core: {core.area:.2f} m² ({core.area/boundary.area*100:.1f}%)")

# 3. Create corridors (Grid pattern - 2×2)
gen = CorridorPatternGenerator(boundary, core)
corridors = gen.generate('grid')  # Use generate(), not select_pattern()
corridor_area = sum(c.area for c in corridors)
print(f"✅ Corridors: {len(corridors)} segments, {corridor_area:.2f} m² ({corridor_area/boundary.area*100:.1f}%)")

# 4. Initialize V3.1 engine
engine = RowBasedLayoutV31(boundary, corridors, core)
print(f"✅ Available for units: {engine.available_area.area:.2f} m²")

# 5. Define unit constraints
unit_constraints = {
    'generation_strategy': 'fill_available',
    'units': [
        {
            'type': 'Studio',
            'percentage': 20,
            'area': {'min': 25, 'target': 30, 'max': 35}
        },
        {
            'type': '1BR',
            'percentage': 40,
            'area': {'min': 45, 'target': 55, 'max': 65}
        },
        {
            'type': '2BR',
            'percentage': 30,
            'area': {'min': 65, 'target': 75, 'max': 85}
        },
        {
            'type': '3BR',
            'percentage': 10,
            'area': {'min': 85, 'target': 100, 'max': 115}
        }
    ]
}

# 6. Layout units
start_time = time.time()
units = engine.layout_units_row_based(unit_constraints)
elapsed = time.time() - start_time

# 7. Calculate metrics
units_area = sum(u['area'] for u in units)
total_used = core.area + corridor_area + units_area
wasted = boundary.area - total_used

print("\n" + "=" * 70)
print("RESULTS - V3.1 SIMPLIFIED")
print("=" * 70)
print(f"📊 Space Allocation:")
print(f"   - Boundary:      {boundary.area:>8.1f} m² (100.0%)")
print(f"   - Core:          {core.area:>8.1f} m² ({core.area/boundary.area*100:>5.1f}%)")
print(f"   - Corridors:     {corridor_area:>8.1f} m² ({corridor_area/boundary.area*100:>5.1f}%)")
print(f"   - Units:         {units_area:>8.1f} m² ({units_area/boundary.area*100:>5.1f}%)")
print(f"   - TOTAL USED:    {total_used:>8.1f} m² ({total_used/boundary.area*100:>5.1f}%)")
print(f"   - WASTED:        {wasted:>8.1f} m² ({wasted/boundary.area*100:>5.1f}%)")

print(f"\n📦 Units Breakdown:")
unit_types = {}
for u in units:
    t = u['type']
    unit_types[t] = unit_types.get(t, 0) + 1

total_units = len(units)
for unit_type in ['Studio', '1BR', '2BR', '3BR']:
    count = unit_types.get(unit_type, 0)
    pct = count / total_units * 100 if total_units > 0 else 0
    print(f"   - {unit_type:8s}: {count:>3d} units ({pct:>5.1f}%)")
print(f"   - TOTAL:       {total_units:>3d} units")

print(f"\n⏱️  Generation Time: {elapsed:.1f}s")

# 8. Success criteria
print("\n" + "=" * 70)
print("SUCCESS CRITERIA - V3.1 (95%+ Coverage Target)")
print("=" * 70)

criteria = {
    'Total Coverage ≥95%': (total_used/boundary.area*100 >= 95, f"{total_used/boundary.area*100:.1f}%"),
    'Wasted <5%': (wasted/boundary.area*100 < 5, f"{wasted/boundary.area*100:.1f}%"),
    'Units ≥45': (total_units >= 45, f"{total_units} units"),
    'Efficiency ≥85%': (units_area/boundary.area*100 >= 85, f"{units_area/boundary.area*100:.1f}%"),
    'Corridors 8-12%': (8 <= corridor_area/boundary.area*100 <= 12, f"{corridor_area/boundary.area*100:.1f}%"),
    'Time <30s': (elapsed < 30, f"{elapsed:.1f}s")
}

all_passed = True
for criterion, (passed, value) in criteria.items():
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {criterion}: {value}")
    if not passed:
        all_passed = False

print("\n" + "=" * 70)
if all_passed:
    print("🎉 V3.1 SUCCESS - All criteria passed!")
else:
    coverage_pct = total_used/boundary.area*100
    print(f"⚠️  V3.1 PARTIAL - {coverage_pct:.1f}% coverage")
    
    # Compare with V2.5.1
    print(f"\n📊 Comparison:")
    print(f"   - V2.5.1 (Region-Based): 66-77% coverage, 33-38 units")
    print(f"   - V3.1 (Row-Based):      {coverage_pct:.1f}% coverage, {total_units} units")
    
    improvement = coverage_pct - 70  # Compare to V2.5.1 average
    if improvement > 0:
        print(f"   - Improvement: +{improvement:.1f}%")
    else:
        print(f"   - No improvement: {improvement:.1f}%")

print("=" * 70)
