"""
FloorPlanGen - DXF Reader Module
Reads DXF files and extracts boundaries, obstacles, and constraints.
"""

import ezdxf
from shapely.geometry import Polygon, Point, LineString, MultiPolygon
from shapely.ops import unary_union
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class DXFReader:
    """Reads and parses DXF files for floor plan generation."""
    
    def __init__(self):
        self.doc = None
        self.modelspace = None
    
    def load_dxf(self, file_path: str) -> bool:
        """Load a DXF file."""
        try:
            self.doc = ezdxf.readfile(file_path)
            self.modelspace = self.doc.modelspace()
            logger.info(f"Successfully loaded DXF file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load DXF file: {e}")
            return False
    
    def extract_boundary(self, layer_name: str = "BOUNDARY") -> Optional[Polygon]:
        """
        Extract the boundary polygon from a specific layer.
        Expects closed polylines or lwpolylines.
        Auto-detects layer if not found on specified layer.
        """
        try:
            boundaries = []
            
            # Try specified layer first
            for entity in self.modelspace.query(f'*[layer=="{layer_name}"]'):
                if entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                    points = []
                    
                    if entity.dxftype() == 'LWPOLYLINE':
                        # Get points from LWPOLYLINE
                        for point in entity.get_points('xy'):
                            points.append((point[0], point[1]))
                    else:
                        # Get points from POLYLINE
                        for vertex in entity.vertices:
                            points.append((vertex.dxf.location.x, vertex.dxf.location.y))
                    
                    if len(points) >= 3:
                        # Close the polygon if not already closed
                        if points[0] != points[-1]:
                            points.append(points[0])
                        
                        polygon = Polygon(points)
                        if polygon.is_valid:
                            boundaries.append(polygon)
            
            # If no boundary found on specified layer, try all layers
            if not boundaries:
                logger.warning(f"No boundaries found on layer '{layer_name}', trying all layers...")
                
                all_layers = self.get_layers()
                for layer in all_layers:
                    if layer == layer_name:  # Skip already tried layer
                        continue
                    
                    for entity in self.modelspace.query(f'*[layer=="{layer}"]'):
                        if entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                            points = []
                            
                            if entity.dxftype() == 'LWPOLYLINE':
                                for point in entity.get_points('xy'):
                                    points.append((point[0], point[1]))
                            else:
                                for vertex in entity.vertices:
                                    points.append((vertex.dxf.location.x, vertex.dxf.location.y))
                            
                            if len(points) >= 3:
                                if points[0] != points[-1]:
                                    points.append(points[0])
                                
                                polygon = Polygon(points)
                                if polygon.is_valid and polygon.area > 10:  # Minimum 10 m²
                                    boundaries.append(polygon)
                                    logger.info(f"Found boundary on layer '{layer}': {polygon.area:.2f} m²")
            
            if not boundaries:
                logger.warning(f"No valid boundaries found in any layer")
                return None
            
            # If multiple boundaries, use the largest one
            if len(boundaries) > 1:
                boundary = max(boundaries, key=lambda p: p.area)
                logger.info(f"Multiple boundaries found, using largest: {boundary.area:.2f} m²")
            else:
                boundary = boundaries[0]
            
            logger.info(f"Extracted boundary: area = {boundary.area:.2f} m², vertices = {len(boundary.exterior.coords)}")
            return boundary
            
        except Exception as e:
            logger.error(f"Failed to extract boundary: {e}")
            return None
    
    def extract_obstacles(self, layer_names: List[str] = None) -> List[Polygon]:
        """
        Extract obstacles (columns, voids, no-build zones) from specified layers.
        """
        if layer_names is None:
            layer_names = ["COLUMNS", "VOID", "NO_BUILD", "OBSTACLES"]
        
        obstacles = []
        
        try:
            for layer_name in layer_names:
                for entity in self.modelspace.query(f'*[layer=="{layer_name}"]'):
                    if entity.dxftype() == 'CIRCLE':
                        # Circular columns
                        center = (entity.dxf.center.x, entity.dxf.center.y)
                        radius = entity.dxf.radius
                        circle = Point(center).buffer(radius)
                        obstacles.append(circle)
                    
                    elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                        # Polygonal obstacles
                        points = []
                        
                        if entity.dxftype() == 'LWPOLYLINE':
                            for point in entity.get_points('xy'):
                                points.append((point[0], point[1]))
                        else:
                            for vertex in entity.vertices:
                                points.append((vertex.dxf.location.x, vertex.dxf.location.y))
                        
                        if len(points) >= 3:
                            if points[0] != points[-1]:
                                points.append(points[0])
                            polygon = Polygon(points)
                            if polygon.is_valid:
                                obstacles.append(polygon)
                    
                    elif entity.dxftype() == 'INSERT':
                        # Block references (like column symbols)
                        insert_point = (entity.dxf.insert.x, entity.dxf.insert.y)
                        # Assume 0.4m x 0.4m column as default
                        size = 0.4
                        column = Point(insert_point).buffer(size / 2, cap_style=3)
                        obstacles.append(column)
            
            logger.info(f"Extracted {len(obstacles)} obstacles")
            return obstacles
            
        except Exception as e:
            logger.error(f"Failed to extract obstacles: {e}")
            return []
    
    def extract_fixed_elements(self, layer_names: List[str] = None) -> Dict[str, List[Polygon]]:
        """
        Extract fixed elements like cores, stairs, elevators.
        """
        if layer_names is None:
            layer_names = ["CORE", "STAIRS", "ELEVATORS", "SHAFTS"]
        
        fixed_elements = {
            "core": [],
            "stairs": [],
            "elevators": [],
            "shafts": []
        }
        
        try:
            for layer_name in layer_names:
                elements = []
                
                for entity in self.modelspace.query(f'*[layer=="{layer_name}"]'):
                    if entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                        points = []
                        
                        if entity.dxftype() == 'LWPOLYLINE':
                            for point in entity.get_points('xy'):
                                points.append((point[0], point[1]))
                        else:
                            for vertex in entity.vertices:
                                points.append((vertex.dxf.location.x, vertex.dxf.location.y))
                        
                        if len(points) >= 3:
                            if points[0] != points[-1]:
                                points.append(points[0])
                            polygon = Polygon(points)
                            if polygon.is_valid:
                                elements.append(polygon)
                
                # Map layer name to element type
                layer_lower = layer_name.lower()
                if "core" in layer_lower:
                    fixed_elements["core"].extend(elements)
                elif "stair" in layer_lower:
                    fixed_elements["stairs"].extend(elements)
                elif "elevator" in layer_lower:
                    fixed_elements["elevators"].extend(elements)
                elif "shaft" in layer_lower:
                    fixed_elements["shafts"].extend(elements)
            
            logger.info(f"Extracted fixed elements: {sum(len(v) for v in fixed_elements.values())} total")
            return fixed_elements
            
        except Exception as e:
            logger.error(f"Failed to extract fixed elements: {e}")
            return fixed_elements
    
    def get_layers(self) -> List[str]:
        """Get all layer names in the DXF file."""
        if not self.doc:
            return []
        return [layer.dxf.name for layer in self.doc.layers]
    
    def get_bounds(self, polygon: Polygon) -> Tuple[float, float, float, float]:
        """Get bounding box of a polygon (minx, miny, maxx, maxy)."""
        return polygon.bounds
    
    def calculate_area(self, polygon: Polygon) -> float:
        """Calculate area of a polygon in square meters."""
        return polygon.area
