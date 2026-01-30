"""Detailed debug of fill_row_with_units"""
import sys
sys.path.append('/home/user/webapp')
from shapely.geometry import Polygon, box

# Simulate row
row_poly = box(0, 0, 50, 8)  # 50m × 8m = 400 m²
row = {
    'polygon': row_poly,
    'direction': 'horizontal',
    'corridor': Polygon()
}

unit_specs = [
    {"type": "Studio", "target_area": 30},
    {"type": "1BR", "target_area": 55},
]

print(f"Row: {row_poly.area:.1f} m²")
print(f"Direction: {row['direction']}")

minx, miny, maxx, maxy = row_poly.bounds
print(f"Bounds: ({minx}, {miny}) to ({maxx}, {maxy})")

row_length = maxx - minx
row_depth = maxy - miny

print(f"Row length: {row_length:.1f}m")
print(f"Row depth: {row_depth:.1f}m")

current_pos = minx
end_pos = maxx

for spec in unit_specs:
    target_area = spec['target_area']
    unit_type = spec['type']
    unit_width = target_area / row_depth
    
    print(f"\n{unit_type} (target {target_area} m²):")
    print(f"  Calculated width: {unit_width:.1f}m (area / depth = {target_area} / {row_depth})")
    print(f"  Current position: {current_pos:.1f}m")
    print(f"  End position: {end_pos:.1f}m")
    print(f"  Fits? {current_pos + unit_width} <= {end_pos}: {current_pos + unit_width <= end_pos}")
    
    if current_pos + unit_width <= end_pos:
        unit_poly = box(current_pos, miny, current_pos + unit_width, maxy)
        print(f"  Created unit: area = {unit_poly.area:.1f} m²")
        current_pos += unit_width
    else:
        print(f"  SKIPPED: doesn't fit")
