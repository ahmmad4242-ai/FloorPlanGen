"""
FloorPlanGen - SVG Generator
Generates SVG previews for quick visualization in UI.
"""

from shapely.geometry import Polygon, Point
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class SVGGenerator:
    """Generates SVG previews from floor plan data."""
    
    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.svg_content = []
    
    def _polygon_to_svg_path(self, polygon: Polygon, scale: float, offset_x: float, offset_y: float) -> str:
        """Convert Shapely polygon to SVG path string."""
        coords = list(polygon.exterior.coords)
        if not coords:
            return ""
        
        # Start with first point
        x, y = coords[0]
        path = f"M {x * scale + offset_x} {offset_y - y * scale}"
        
        # Line to remaining points
        for x, y in coords[1:]:
            path += f" L {x * scale + offset_x} {offset_y - y * scale}"
        
        path += " Z"  # Close path
        return path
    
    def generate_svg(self, 
                    boundary: Polygon,
                    core: Polygon,
                    corridors: List[Polygon],
                    units: List[Dict]) -> str:
        """
        Generate SVG preview from floor plan components.
        
        Args:
            boundary: Floor boundary polygon
            core: Building core polygon
            corridors: List of corridor polygons
            units: List of unit dictionaries with polygon data
        
        Returns:
            SVG string
        """
        try:
            # Calculate bounds and scale
            bounds = boundary.bounds
            minx, miny, maxx, maxy = bounds
            
            width_m = maxx - minx
            height_m = maxy - miny
            
            # Calculate scale to fit in viewport with padding
            padding = 40
            scale_x = (self.width - 2 * padding) / width_m
            scale_y = (self.height - 2 * padding) / height_m
            scale = min(scale_x, scale_y)
            
            # Calculate offsets to center
            offset_x = padding - minx * scale + (self.width - width_m * scale) / 2
            offset_y = self.height - padding + miny * scale - (self.height - height_m * scale) / 2
            
            # Start SVG
            svg = [
                f'<svg width="{self.width}" height="{self.height}" xmlns="http://www.w3.org/2000/svg">',
                '<defs>',
                '  <style>',
                '    .boundary { fill: none; stroke: #333; stroke-width: 2; }',
                '    .core { fill: #E91E63; fill-opacity: 0.3; stroke: #E91E63; stroke-width: 1.5; }',
                '    .corridor { fill: #2196F3; fill-opacity: 0.2; stroke: #2196F3; stroke-width: 1; }',
                '    .unit { fill: #FFF9C4; fill-opacity: 0.6; stroke: #F57C00; stroke-width: 1; }',
                '    .unit-label { font-family: Arial; font-size: 10px; fill: #333; text-anchor: middle; }',
                '  </style>',
                '</defs>',
                '<rect width="100%" height="100%" fill="#f5f5f5"/>'
            ]
            
            # Add boundary
            boundary_path = self._polygon_to_svg_path(boundary, scale, offset_x, offset_y)
            svg.append(f'<path d="{boundary_path}" class="boundary"/>')
            
            # Add corridors
            for corridor in corridors:
                corridor_path = self._polygon_to_svg_path(corridor, scale, offset_x, offset_y)
                svg.append(f'<path d="{corridor_path}" class="corridor"/>')
            
            # Add core
            if core:
                core_path = self._polygon_to_svg_path(core, scale, offset_x, offset_y)
                svg.append(f'<path d="{core_path}" class="core"/>')
            
            # Add units with labels
            for unit in units:
                unit_poly = unit["polygon"]
                unit_path = self._polygon_to_svg_path(unit_poly, scale, offset_x, offset_y)
                svg.append(f'<path d="{unit_path}" class="unit"/>')
                
                # Add label at centroid
                centroid = unit_poly.centroid
                label_x = centroid.x * scale + offset_x
                label_y = offset_y - centroid.y * scale
                
                unit_type = unit.get("type", "Unit")
                area = unit.get("area", 0)
                
                svg.append(
                    f'<text x="{label_x}" y="{label_y}" class="unit-label">'
                    f'{unit_type}<tspan x="{label_x}" dy="12">{area:.0f}m²</tspan>'
                    '</text>'
                )
            
            # Add title
            svg.append(
                f'<text x="{self.width/2}" y="25" '
                f'style="font-family: Arial; font-size: 16px; font-weight: bold; '
                f'fill: #333; text-anchor: middle;">Floor Plan Preview</text>'
            )
            
            svg.append('</svg>')
            
            svg_string = '\n'.join(svg)
            logger.info(f"Generated SVG preview: {len(units)} units")
            return svg_string
            
        except Exception as e:
            logger.error(f"Failed to generate SVG: {e}")
            return self._generate_error_svg(str(e))
    
    def _generate_error_svg(self, error_message: str) -> str:
        """Generate error SVG."""
        return f'''<svg width="{self.width}" height="{self.height}" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#ffebee"/>
            <text x="{self.width/2}" y="{self.height/2}" 
                  style="font-family: Arial; font-size: 14px; fill: #c62828; text-anchor: middle;">
                Error generating preview: {error_message}
            </text>
        </svg>'''
