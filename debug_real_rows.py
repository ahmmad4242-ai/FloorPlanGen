"""Debug actual row geometry"""
import sys
sys.path.append('/home/user/webapp')
from shapely.geometry import Polygon
from app.professional_layout_engine import ProfessionalLayoutEngine
from app.corridor_patterns import CorridorPatternGenerator
from app.row_based_layout_v3 import RowBasedLayoutV3

boundary_coords = [(0, 0), (70.4, 0), (70.4, 10), (60, 10), (60, 50.4), (10, 50.4), (10, 40), (0, 40)]
boundary = Polygon(boundary_coords)

engine = ProfessionalLayoutEngine(boundary, [])
cores = engine.place_cores(core_count=1, core_area=40.0)
core = cores[0]

corridor_gen = CorridorPatternGenerator(boundary, core, corridor_width=2.3)
corridors = corridor_gen.generate(pattern='H')

v3 = RowBasedLayoutV3(boundary, corridors, core)
rows = v3.split_into_rows(unit_depth_avg=8.0)

print(f"Total available area: {v3.available_area.area:.1f} m²")
print(f"\nRows created: {len(rows)}")

for i, row in enumerate(rows):
    minx, miny, maxx, maxy = row['polygon'].bounds
    if row['direction'] == 'horizontal':
        length = maxx - minx
        depth = maxy - miny
    else:
        length = maxy - miny
        depth = maxx - minx
    
    print(f"\nRow {i+1}:")
    print(f"  Area: {row['polygon'].area:.1f} m²")
    print(f"  Direction: {row['direction']}")
    print(f"  Length: {length:.1f}m, Depth: {depth:.1f}m")
    print(f"  Bounds: ({minx:.1f}, {miny:.1f}) to ({maxx:.1f}, {maxy:.1f})")

# Try filling first row
if rows:
    print(f"\n{'='*60}")
    print("Testing fill_row_with_units on Row 1:")
    unit_specs = [
        {"type": "Studio", "target_area": 30},
        {"type": "1BR", "target_area": 55},
        {"type": "2BR", "target_area": 75},
    ]
    placed = v3.fill_row_with_units(rows[0], unit_specs)
    print(f"Placed: {len(placed)} units")
    for u in placed:
        print(f"  - {u['type']}: {u['area']:.1f} m²")
