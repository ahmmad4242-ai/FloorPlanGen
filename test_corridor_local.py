#!/usr/bin/env python3
"""
Quick local test for corridor adjacency improvements
"""
import sys
import numpy as np
from shapely.geometry import box, Point
from shapely.ops import unary_union

# Add app to path
sys.path.insert(0, '/home/user/webapp/app')

from professional_layout_engine import ProfessionalLayoutEngine

def test_corridor_adjacency():
    """Test that units are properly adjacent to corridors"""
    print("\n" + "="*60)
    print("🧪 TESTING CORRIDOR ADJACENCY V2.1")
    print("="*60 + "\n")
    
    # Create a simple rectangular building
    boundary = box(0, 0, 40, 30)  # 40m × 30m = 1200 m²
    
    print(f"📐 Building: {boundary.area:.1f} m² (40m × 30m)")
    
    # Initialize engine (boundary, obstacles)
    engine = ProfessionalLayoutEngine(boundary, [])
    
    # Place core
    print(f"\n1️⃣ Placing core...")
    core = engine.place_core(core_area=50, preferred_location='center')
    print(f"   ✅ Core: {core.area:.1f} m²")
    
    # Create corridor network
    print(f"\n2️⃣ Creating corridor network...")
    corridors = engine.create_visible_corridor_network(core, corridor_width=2.2)
    corridor_area = sum(c.area for c in corridors)
    corridor_ratio = corridor_area / boundary.area * 100
    print(f"   ✅ Corridors: {len(corridors)} segments")
    print(f"   ✅ Area: {corridor_area:.1f} m² ({corridor_ratio:.1f}%)")
    
    # Layout units with V2 constraints
    print(f"\n3️⃣ Placing units with strict adjacency...")
    unit_constraints = {
        "generation_strategy": "fill_available",
        "units": [
            {
                "type": "Studio",
                "percentage": 20,
                "priority": 1,
                "area": {"min": 25, "target": 30, "max": 35}
            },
            {
                "type": "1BR",
                "percentage": 40,
                "priority": 2,
                "area": {"min": 45, "target": 55, "max": 65}
            },
            {
                "type": "2BR",
                "percentage": 30,
                "priority": 3,
                "area": {"min": 65, "target": 75, "max": 85}
            },
            {
                "type": "3BR",
                "percentage": 10,
                "priority": 4,
                "area": {"min": 85, "target": 97, "max": 110}
            }
        ],
        "total_units": {"min": 15, "max": 40}
    }
    
    units = engine.layout_units_with_corridor_access(core, corridors, unit_constraints)
    
    # Analyze results
    print(f"\n" + "="*60)
    print("📊 RESULTS ANALYSIS")
    print("="*60 + "\n")
    
    print(f"✅ Total Units: {len(units)}")
    
    # Count by type
    units_by_type = {}
    for unit in units:
        ut = unit["type"]
        units_by_type[ut] = units_by_type.get(ut, 0) + 1
    
    print(f"\n📦 Units by Type:")
    total_target = len(units)
    for unit_type, count in sorted(units_by_type.items()):
        percentage = (count / total_target * 100) if total_target > 0 else 0
        print(f"   {unit_type}: {count} units ({percentage:.1f}%)")
    
    # Check corridor distances
    print(f"\n🎯 Corridor Adjacency Analysis:")
    corridor_union = unary_union(corridors)
    
    distances = []
    touching_count = 0
    for unit in units:
        poly = unit["polygon"]
        dist = poly.distance(corridor_union)
        distances.append(dist)
        
        # Check if touching (shared edge)
        contact = poly.intersection(corridor_union.buffer(0.05))
        if not contact.is_empty and contact.area < 0.1:
            touching_count += 1
    
    if distances:
        print(f"   Min distance: {min(distances):.2f} m")
        print(f"   Max distance: {max(distances):.2f} m")
        print(f"   Avg distance: {np.mean(distances):.2f} m")
        print(f"   Median distance: {np.median(distances):.2f} m")
        print(f"   Touching corridor: {touching_count}/{len(units)} ({touching_count/len(units)*100:.1f}%)")
    
    # Check spacing
    print(f"\n📏 Unit Spacing Analysis:")
    min_spacing = float('inf')
    for i, unit1 in enumerate(units):
        for unit2 in units[i+1:]:
            spacing = unit1["polygon"].distance(unit2["polygon"])
            if spacing < min_spacing:
                min_spacing = spacing
    
    if min_spacing < float('inf'):
        print(f"   Min spacing: {min_spacing:.2f} m")
        print(f"   Expected: 0.25 m (wall thickness)")
        if min_spacing >= 0.20:
            print(f"   ✅ PASS: Proper spacing maintained")
        else:
            print(f"   ⚠️ WARNING: Spacing too small")
    
    # Overall metrics
    print(f"\n📈 Overall Metrics:")
    units_area = sum(u["area"] for u in units)
    efficiency = units_area / boundary.area * 100
    print(f"   Units area: {units_area:.1f} m² ({efficiency:.1f}%)")
    print(f"   Corridor area: {corridor_area:.1f} m² ({corridor_ratio:.1f}%)")
    print(f"   Core area: {core.area:.1f} m²")
    
    # Pass/Fail criteria
    print(f"\n" + "="*60)
    print("✅ PASS/FAIL CRITERIA")
    print("="*60 + "\n")
    
    passed = True
    
    # 1. Placement rate
    min_units = unit_constraints["total_units"]["min"]
    if len(units) >= min_units:
        print(f"✅ Placement Rate: {len(units)}/{min_units} = {len(units)/min_units*100:.0f}%")
    else:
        print(f"❌ Placement Rate: {len(units)}/{min_units} = {len(units)/min_units*100:.0f}% (FAIL)")
        passed = False
    
    # 2. Max corridor distance
    if distances and max(distances) <= 2.5:
        print(f"✅ Max Corridor Distance: {max(distances):.2f} m ≤ 2.5 m")
    elif distances:
        print(f"❌ Max Corridor Distance: {max(distances):.2f} m > 2.5 m (FAIL)")
        passed = False
    
    # 3. Touching percentage
    if touching_count / len(units) >= 0.60:  # At least 60% should touch
        print(f"✅ Corridor Contact: {touching_count/len(units)*100:.1f}% ≥ 60%")
    else:
        print(f"⚠️ Corridor Contact: {touching_count/len(units)*100:.1f}% < 60% (WARNING)")
    
    # 4. Corridor ratio
    if 8 <= corridor_ratio <= 15:
        print(f"✅ Corridor Ratio: {corridor_ratio:.1f}% (8-15% target)")
    else:
        print(f"⚠️ Corridor Ratio: {corridor_ratio:.1f}% (outside 8-15% target)")
    
    # 5. Efficiency
    if efficiency >= 50:
        print(f"✅ Efficiency: {efficiency:.1f}% ≥ 50%")
    else:
        print(f"⚠️ Efficiency: {efficiency:.1f}% < 50% (WARNING)")
    
    print(f"\n" + "="*60)
    if passed:
        print("🎉 ALL CRITICAL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*60 + "\n")
    
    return passed

if __name__ == "__main__":
    try:
        success = test_corridor_adjacency()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
