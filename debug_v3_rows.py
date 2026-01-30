"""Debug V3.0 row creation"""
import sys
sys.path.append('/home/user/webapp')
from shapely.geometry import Polygon
from app.professional_layout_engine import ProfessionalLayoutEngine
from app.corridor_patterns import CorridorPatternGenerator
from app.row_based_layout_v3 import RowBasedLayoutV3

# Test boundary
boundary_coords = [(0, 0), (70.4, 0), (70.4, 10), (60, 10), (60, 50.4), (10, 50.4), (10, 40), (0, 40)]
boundary = Polygon(boundary_coords)

engine = ProfessionalLayoutEngine(boundary, [])
cores = engine.place_cores(core_count=1, core_area=40.0)
core = cores[0]

corridor_gen = CorridorPatternGenerator(boundary, core, corridor_width=2.3)
corridors = corridor_gen.generate(pattern='H')

# Initialize V3.0
v3 = RowBasedLayoutV3(boundary, corridors, core)

# Test row creation
rows = v3.split_into_rows(unit_depth_avg=8.0)

print(f"Created {len(rows)} rows:")
for i, row in enumerate(rows):
    print(f"  Row {i+1}: area={row['polygon'].area:.1f} m², direction={row['direction']}")

# Test with unit specs
unit_specs = [
    {"type": "Studio", "target_area": 30},
    {"type": "1BR", "target_area": 55},
]

print(f"\nTesting fill_row_with_units with {len(unit_specs)} specs:")
if rows:
    placed = v3.fill_row_with_units(rows[0], unit_specs)
    print(f"  Placed {len(placed)} units in first row")
    for u in placed:
        print(f"    - {u['type']}: {u['area']:.1f} m²")
