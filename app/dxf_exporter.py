"""
FloorPlanGen - DXF Exporter
Exports generated floor plans to DXF with organized layers.
"""

import ezdxf
from ezdxf.enums import TextEntityAlignment
from shapely.geometry import Polygon, Point
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class DXFExporter:
    """Exports floor plans to DXF format with organized layers."""
    
    # Standard layer definitions
    LAYERS = {
        "BOUNDARY": {"color": 7},  # White
        "WALLS": {"color": 1},     # Red
        "DOORS": {"color": 3},     # Green
        "WINDOWS": {"color": 4},   # Cyan
        "CORRIDORS": {"color": 5}, # Blue
        "CORE": {"color": 6},      # Magenta
        "UNITS": {"color": 2},     # Yellow
        "DIMENSIONS": {"color": 8}, # Dark Gray
        "TEXT": {"color": 7},      # White
        "FURNITURE": {"color": 9}  # Light Gray
    }
    
    def __init__(self):
        self.doc = None
        self.modelspace = None
    
    def create_new_drawing(self) -> None:
        """Create a new DXF document."""
        self.doc = ezdxf.new('R2010')
        self.modelspace = self.doc.modelspace()
        
        # Create layers
        for layer_name, props in self.LAYERS.items():
            self.doc.layers.add(layer_name, color=props["color"])
        
        logger.info("Created new DXF document with standard layers")
    
    def add_boundary(self, boundary: Polygon) -> None:
        """Add boundary polygon to BOUNDARY layer."""
        try:
            coords = list(boundary.exterior.coords)
            self.modelspace.add_lwpolyline(
                coords,
                dxfattribs={'layer': 'BOUNDARY', 'closed': True}
            )
            logger.info("Added boundary to DXF")
        except Exception as e:
            logger.error(f"Failed to add boundary: {e}")
    
    def add_core(self, core: Polygon) -> None:
        """Add core polygon to CORE layer."""
        try:
            coords = list(core.exterior.coords)
            self.modelspace.add_lwpolyline(
                coords,
                dxfattribs={'layer': 'CORE', 'closed': True}
            )
            
            # Add hatch pattern
            hatch = self.modelspace.add_hatch(color=6)
            hatch.paths.add_polyline_path(coords, is_closed=True)
            hatch.set_pattern_fill("ANSI31", scale=0.5)
            hatch.dxf.layer = 'CORE'
            
            logger.info("Added core to DXF")
        except Exception as e:
            logger.error(f"Failed to add core: {e}")
    
    def add_corridors(self, corridors: List[Polygon]) -> None:
        """Add corridor polygons to CORRIDORS layer."""
        try:
            for corridor in corridors:
                coords = list(corridor.exterior.coords)
                self.modelspace.add_lwpolyline(
                    coords,
                    dxfattribs={'layer': 'CORRIDORS', 'closed': True}
                )
            
            logger.info(f"Added {len(corridors)} corridors to DXF")
        except Exception as e:
            logger.error(f"Failed to add corridors: {e}")
    
    def add_units(self, units: List[Dict]) -> None:
        """Add unit polygons to UNITS layer with labels."""
        try:
            for unit in units:
                polygon = unit["polygon"]
                unit_id = unit["id"]
                unit_type = unit["type"]
                area = unit["area"]
                
                # Add unit boundary
                coords = list(polygon.exterior.coords)
                self.modelspace.add_lwpolyline(
                    coords,
                    dxfattribs={'layer': 'UNITS', 'closed': True}
                )
                
                # Add unit label at centroid
                centroid = polygon.centroid
                label_text = f"{unit_type}\n{area:.1f}m²"
                
                self.modelspace.add_mtext(
                    label_text,
                    dxfattribs={
                        'layer': 'TEXT',
                        'char_height': 1.5,
                        'insert': (centroid.x, centroid.y),
                        'attachment_point': 5  # Middle center
                    }
                )
            
            logger.info(f"Added {len(units)} units to DXF")
        except Exception as e:
            logger.error(f"Failed to add units: {e}")
    
    def add_walls(self, units: List[Dict], wall_thickness: float) -> None:
        """Add walls between units to WALLS layer."""
        try:
            for unit in units:
                polygon = unit["polygon"]
                
                # Create offset for wall thickness
                outer = polygon.buffer(wall_thickness / 2)
                inner = polygon.buffer(-wall_thickness / 2)
                
                # Add outer wall
                coords = list(outer.exterior.coords)
                self.modelspace.add_lwpolyline(
                    coords,
                    dxfattribs={'layer': 'WALLS', 'closed': True}
                )
            
            logger.info(f"Added walls for {len(units)} units to DXF")
        except Exception as e:
            logger.error(f"Failed to add walls: {e}")
    
    def add_doors(self, units: List[Dict], corridors: List[Polygon], 
                  door_width: float) -> None:
        """
        Add doors between units and corridors to DOORS layer.
        
        Args:
            units: List of unit dictionaries with polygon data
            corridors: List of corridor polygons
            door_width: Door width in meters
        """
        try:
            from shapely.geometry import LineString
            import numpy as np
            
            doors_added = 0
            
            for unit in units:
                unit_poly = unit["polygon"]
                
                # Find the corridor closest to this unit
                min_dist = float('inf')
                closest_corridor = None
                closest_point = None
                
                for corridor in corridors:
                    # Find intersection line between unit and corridor
                    if unit_poly.touches(corridor) or unit_poly.intersects(corridor):
                        # Get the shared boundary
                        intersection = unit_poly.boundary.intersection(corridor.boundary)
                        
                        if intersection.length > door_width:
                            # Find midpoint for door placement
                            if hasattr(intersection, 'coords'):
                                coords = list(intersection.coords)
                                mid_idx = len(coords) // 2
                                door_point = Point(coords[mid_idx])
                            else:
                                door_point = intersection.centroid
                            
                            closest_corridor = corridor
                            closest_point = door_point
                            break
                
                if closest_point:
                    # Create door symbol (arc + line)
                    x, y = closest_point.x, closest_point.y
                    
                    # Door opening line
                    self.modelspace.add_line(
                        (x - door_width/2, y),
                        (x + door_width/2, y),
                        dxfattribs={'layer': 'DOORS', 'color': 3}
                    )
                    
                    # Door swing arc (90 degree arc)
                    self.modelspace.add_arc(
                        center=(x - door_width/2, y),
                        radius=door_width,
                        start_angle=0,
                        end_angle=90,
                        dxfattribs={'layer': 'DOORS', 'color': 3}
                    )
                    
                    doors_added += 1
            
            logger.info(f"Added {doors_added} doors to DXF")
        except Exception as e:
            logger.error(f"Failed to add doors: {e}")
    
    def add_dimensions(self, boundary: Polygon) -> None:
        """Add dimensions to DIMENSIONS layer."""
        try:
            bounds = boundary.bounds
            minx, miny, maxx, maxy = bounds
            
            # Overall width dimension
            self.modelspace.add_linear_dim(
                base=(minx + (maxx - minx) / 2, miny - 2),
                p1=(minx, miny),
                p2=(maxx, miny),
                dimstyle='EZ_M_100_H25_CM',
                dxfattribs={'layer': 'DIMENSIONS'}
            )
            
            # Overall height dimension
            self.modelspace.add_linear_dim(
                base=(minx - 2, miny + (maxy - miny) / 2),
                p1=(minx, miny),
                p2=(minx, maxy),
                angle=90,
                dimstyle='EZ_M_100_H25_CM',
                dxfattribs={'layer': 'DIMENSIONS'}
            )
            
            logger.info("Added dimensions to DXF")
        except Exception as e:
            logger.error(f"Failed to add dimensions: {e}")
    
    def add_title_block(self, 
                       project_name: str,
                       variant_number: int,
                       area: float,
                       units_count: int) -> None:
        """Add title block with project information."""
        try:
            # Position title block at bottom right
            x, y = 0, 0
            
            # Project name
            self.modelspace.add_text(
                f"Project: {project_name}",
                dxfattribs={
                    'layer': 'TEXT',
                    'height': 3.0,
                    'insert': (x, y - 5)
                }
            )
            
            # Variant number
            self.modelspace.add_text(
                f"Variant: #{variant_number}",
                dxfattribs={
                    'layer': 'TEXT',
                    'height': 2.0,
                    'insert': (x, y - 10)
                }
            )
            
            # Area info
            self.modelspace.add_text(
                f"Total Area: {area:.2f} m²",
                dxfattribs={
                    'layer': 'TEXT',
                    'height': 2.0,
                    'insert': (x, y - 15)
                }
            )
            
            # Units count
            self.modelspace.add_text(
                f"Units: {units_count}",
                dxfattribs={
                    'layer': 'TEXT',
                    'height': 2.0,
                    'insert': (x, y - 20)
                }
            )
            
            logger.info("Added title block to DXF")
        except Exception as e:
            logger.error(f"Failed to add title block: {e}")
    
    def save(self, file_path: str) -> bool:
        """Save DXF document to file."""
        try:
            self.doc.saveas(file_path)
            logger.info(f"Saved DXF to: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save DXF: {e}")
            return False
