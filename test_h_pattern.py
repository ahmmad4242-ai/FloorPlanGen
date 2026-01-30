#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/user/webapp')
from shapely.geometry import Polygon
from app.professional_layout_engine import ProfessionalLayoutEngine
import time

boundary = Polygon([(0,0), (70.4,0), (70.4,10), (60,10), (60,50.4), (10,50.4), (10,40), (0,40), (0,0)])
engine = ProfessionalLayoutEngine(boundary)

cores = engine.place_cores(core_count=1, core_area=40.0)
corridors = engine.create_visible_corridor_network(cores[0], corridor_width=2.5, pattern='H')

unit_constraints = {
    "generation_strategy": "fill_available",
    "units": [
        {"type": "Studio", "percentage": 20, "priority": 2, "area": {"min": 25, "max": 35, "target": 30}},
        {"type": "1BR", "percentage": 40, "priority": 1, "area": {"min": 45, "max": 65, "target": 55}},
        {"type": "2BR", "percentage": 30, "priority": 1, "area": {"min": 65, "max": 85, "target": 75}},
        {"type": "3BR", "percentage": 10, "priority": 3, "area": {"min": 85, "max": 110, "target": 97.5}}
    ],
    "total_units": {"min": 15, "max": 50},
    "distribution_strategy": "balanced"
}

units = engine.layout_units_with_corridor_access(unit_constraints=unit_constraints, core=cores[0], corridors=corridors)

core_area = sum(c.area for c in cores)
corridor_area = sum(c.area for c in corridors)
units_area = sum(u['area'] for u in units)
total = core_area + corridor_area + units_area
coverage = total / boundary.area * 100

print(f"H Pattern Results:")
print(f"  Core: {core_area:.1f} m² ({core_area/boundary.area*100:.1f}%)")
print(f"  Corridors: {corridor_area:.1f} m² ({corridor_area/boundary.area*100:.1f}%)")
print(f"  Units: {len(units)} × {units_area:.1f} m² ({units_area/boundary.area*100:.1f}%)")
print(f"  Total: {total:.1f} m² ({coverage:.1f}%)")
print(f"  Wasted: {boundary.area - total:.1f} m² ({100-coverage:.1f}%)")
print(f"\n  ✅ Coverage ≥95%: {coverage >= 95}")
