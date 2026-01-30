import sys
sys.path.insert(0, '/home/user/webapp')
from shapely.geometry import Polygon
from app.professional_layout_engine import ProfessionalLayoutEngine

boundary = Polygon([(0,0), (70.4,0), (70.4,10), (60,10), (60,50.4), (10,50.4), (10,40), (0,40), (0,0)])
engine = ProfessionalLayoutEngine(boundary)
cores = engine.place_cores(core_count=1, core_area=40.0)

print("=" * 60)
print("Comparing Corridor Patterns")
print("=" * 60)
for pattern in ['H', 'grid', 'U', '+', 'T']:
    corridors = engine.create_visible_corridor_network(cores[0], corridor_width=2.5, pattern=pattern)
    corridor_area = sum(c.area for c in corridors)
    ratio = corridor_area / boundary.area * 100
    print(f'{pattern:6s}: {len(corridors):2d} corridors, {corridor_area:6.1f} m² ({ratio:5.1f}%)')
