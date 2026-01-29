"""
FloorPlanGen - Space Partitioning Algorithm
Divides floor space into units, corridors, and service areas.
"""

from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union, split
from typing import List, Dict, Tuple, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class SpacePartitioner:
    """DEPRECATED: Use ArchitecturalSpacePartitioner instead"""
    pass

class OldSpacePartitioner_Backup:
    """Partitions floor space into functional areas."""
    
    def __init__(self, boundary: Polygon, obstacles: List[Polygon]):
        self.boundary = boundary
        self.obstacles = obstacles
        self.usable_area = self._calculate_usable_area()
    
    def _calculate_usable_area(self) -> Polygon:
        """Calculate usable area by subtracting obstacles from boundary."""
        try:
            if self.obstacles:
                obstacles_union = unary_union(self.obstacles)
                usable = self.boundary.difference(obstacles_union)
            else:
                usable = self.boundary
            
            logger.info(f"Usable area: {usable.area:.2f} m² ({usable.area / self.boundary.area * 100:.1f}%)")
            return usable
        except Exception as e:
            logger.error(f"Failed to calculate usable area: {e}")
            return self.boundary
    
    def place_core(self, 
                   core_area: float = 40.0,
                   preferred_location: str = "center",
                   fixed_core: Optional[Polygon] = None) -> Optional[Polygon]:
        """
        Place the building core (elevators, stairs, shafts).
        
        Args:
            core_area: Target area for core in m²
            preferred_location: "center", "north", "south", "east", "west"
            fixed_core: Pre-defined core polygon (if provided, use this)
        """
        if fixed_core:
            logger.info("Using fixed core from DXF")
            return fixed_core
        
        try:
            # Get boundary centroid
            centroid = self.boundary.centroid
            
            # Adjust position based on preferred location
            bounds = self.boundary.bounds
            minx, miny, maxx, maxy = bounds
            width = maxx - minx
            height = maxy - miny
            
            if preferred_location == "center":
                core_center = centroid
            elif preferred_location == "north":
                core_center = Point(centroid.x, centroid.y + height * 0.25)
            elif preferred_location == "south":
                core_center = Point(centroid.x, centroid.y - height * 0.25)
            elif preferred_location == "east":
                core_center = Point(centroid.x + width * 0.25, centroid.y)
            elif preferred_location == "west":
                core_center = Point(centroid.x - width * 0.25, centroid.y)
            else:
                core_center = centroid
            
            # Create core box
            core_size = np.sqrt(core_area)
            core = box(
                core_center.x - core_size / 2,
                core_center.y - core_size / 2,
                core_center.x + core_size / 2,
                core_center.y + core_size / 2
            )
            
            # Ensure core is within usable area
            if not self.usable_area.contains(core):
                # Try to adjust position
                core = core.intersection(self.usable_area)
            
            logger.info(f"Placed core at {preferred_location}: area = {core.area:.2f} m²")
            return core
            
        except Exception as e:
            logger.error(f"Failed to place core: {e}")
            return None
    
    def create_corridor_network(self,
                                core: Polygon,
                                corridor_width: float = 2.2,
                                layout_type: str = "double_loaded") -> List[Polygon]:
        """
        Create corridor network around the core.
        
        Args:
            core: Core polygon
            corridor_width: Corridor width in meters
            layout_type: "double_loaded", "single_loaded", "circular"
        """
        corridors = []
        
        try:
            if layout_type == "double_loaded":
                # Create corridors on both sides of core
                core_bounds = core.bounds
                minx, miny, maxx, maxy = core_bounds
                
                # Horizontal corridors (north and south)
                north_corridor = box(
                    minx - corridor_width,
                    maxy,
                    maxx + corridor_width,
                    maxy + corridor_width
                )
                south_corridor = box(
                    minx - corridor_width,
                    miny - corridor_width,
                    maxx + corridor_width,
                    miny
                )
                
                # Vertical corridors (east and west)
                east_corridor = box(
                    maxx,
                    miny - corridor_width,
                    maxx + corridor_width,
                    maxy + corridor_width
                )
                west_corridor = box(
                    minx - corridor_width,
                    miny - corridor_width,
                    minx,
                    maxy + corridor_width
                )
                
                corridors = [north_corridor, south_corridor, east_corridor, west_corridor]
            
            elif layout_type == "circular":
                # Create circular corridor around core
                core_centroid = core.centroid
                outer_radius = np.sqrt(core.area / np.pi) + corridor_width
                inner_radius = np.sqrt(core.area / np.pi)
                
                outer_circle = core_centroid.buffer(outer_radius)
                inner_circle = core_centroid.buffer(inner_radius)
                circular_corridor = outer_circle.difference(inner_circle)
                
                corridors = [circular_corridor]
            
            # Clip corridors to usable area
            clipped_corridors = []
            for corridor in corridors:
                clipped = corridor.intersection(self.usable_area)
                if clipped.area > 0:
                    clipped_corridors.append(clipped)
            
            total_corridor_area = sum(c.area for c in clipped_corridors)
            logger.info(f"Created {len(clipped_corridors)} corridors: total area = {total_corridor_area:.2f} m²")
            
            return clipped_corridors
            
        except Exception as e:
            logger.error(f"Failed to create corridor network: {e}")
            return []
    
    def partition_into_units(self,
                            core: Polygon,
                            corridors: List[Polygon],
                            target_unit_areas: List[float],
                            min_unit_width: float = 3.5,
                            unit_types: List[Dict] = None) -> List[Dict]:
        """
        Partition remaining space into residential units with EXACT counts.
        Uses Rectangle Packing algorithm to respect requested unit counts.
        
        Args:
            core: Core polygon
            corridors: List of corridor polygons
            target_unit_areas: List of target areas for each unit (one per requested unit)
            min_unit_width: Minimum unit width in meters
            unit_types: List of unit type configurations with type, min_area, max_area
        """
        units = []
        
        try:
            # Calculate available area for units
            occupied = unary_union([core] + corridors)
            available = self.usable_area.difference(occupied)
            
            if available.area == 0:
                logger.warning("No available area for units")
                return []
            
            logger.info(f"Available area for units: {available.area:.2f}m²")
            logger.info(f"Requested units: {len(target_unit_areas)}")
            
            # Check if enough space
            total_requested_area = sum(target_unit_areas)
            if total_requested_area > available.area * 0.95:  # Allow 5% overhead
                logger.warning(f"Requested area {total_requested_area:.2f}m² exceeds available {available.area:.2f}m²")
                # Scale down unit areas proportionally
                scale_factor = (available.area * 0.90) / total_requested_area
                target_unit_areas = [area * scale_factor for area in target_unit_areas]
                logger.info(f"Scaled down areas by {scale_factor:.2f}x")
            
            # Convert target areas to rectangles (width × height)
            unit_rectangles = []
            for i, target_area in enumerate(target_unit_areas):
                # Calculate dimensions with aspect ratio ~1.2 (slightly rectangular)
                aspect_ratio = 1.2
                unit_width = max(np.sqrt(target_area * aspect_ratio), min_unit_width)
                unit_height = target_area / unit_width
                
                unit_type_info = unit_types[i] if unit_types and i < len(unit_types) else {"type": "Studio", "min_area": 50, "max_area": 100}
                
                unit_rectangles.append({
                    "index": i,
                    "width": unit_width,
                    "height": unit_height,
                    "area": target_area,
                    "type": unit_type_info.get("type", "Studio"),
                    "placed": False,
                    "polygon": None
                })
            
            # Sort rectangles by area (largest first) for better packing
            unit_rectangles.sort(key=lambda x: x["area"], reverse=True)
            
            # Get available bounds
            bounds = available.bounds
            minx, miny, maxx, maxy = bounds
            container_width = maxx - minx
            container_height = maxy - miny
            
            logger.info(f"Container size: {container_width:.2f}m × {container_height:.2f}m")
            
            # First-Fit Decreasing Height (FFDH) Packing Algorithm
            # This ensures we place ALL requested units
            levels = []  # Each level: {"y": y_position, "height": level_height, "x": current_x, "units": [...]}
            
            for rect in unit_rectangles:
                placed = False
                
                # Try to place in existing levels
                for level in levels:
                    # Check if rectangle fits in current level
                    if (level["x"] + rect["width"] <= container_width and 
                        rect["height"] <= level["height"]):
                        
                        # Create polygon at this position
                        x1 = minx + level["x"]
                        y1 = level["y"]
                        x2 = x1 + rect["width"]
                        y2 = y1 + rect["height"]
                        
                        unit_box = box(x1, y1, x2, y2)
                        unit_polygon = unit_box.intersection(available)
                        
                        if unit_polygon.area > rect["area"] * 0.7:  # At least 70% of target area
                            rect["polygon"] = unit_polygon
                            rect["placed"] = True
                            level["x"] += rect["width"]
                            level["units"].append(rect)
                            placed = True
                            break
                
                # If not placed, create new level
                if not placed:
                    new_level_y = sum(l["height"] for l in levels)
                    
                    if new_level_y + rect["height"] <= container_height:
                        # Place at start of new level
                        x1 = minx
                        y1 = miny + new_level_y
                        x2 = x1 + rect["width"]
                        y2 = y1 + rect["height"]
                        
                        unit_box = box(x1, y1, x2, y2)
                        unit_polygon = unit_box.intersection(available)
                        
                        if unit_polygon.area > rect["area"] * 0.7:
                            rect["polygon"] = unit_polygon
                            rect["placed"] = True
                            
                            new_level = {
                                "y": new_level_y,
                                "height": rect["height"],
                                "x": rect["width"],
                                "units": [rect]
                            }
                            levels.append(new_level)
                            placed = True
                
                if not placed:
                    logger.warning(f"Failed to place unit {rect['index']} (area={rect['area']:.2f}m²)")
            
            # Build final units list in original order
            unit_rectangles.sort(key=lambda x: x["index"])
            
            unit_id = 1
            for rect in unit_rectangles:
                if rect["placed"] and rect["polygon"]:
                    units.append({
                        "id": f"unit_{unit_id}",
                        "type": rect["type"],
                        "polygon": rect["polygon"],
                        "area": rect["polygon"].area,
                        "centroid": rect["polygon"].centroid
                    })
                    unit_id += 1
            
            logger.info(f"Successfully placed {len(units)}/{len(target_unit_areas)} units")
            
            # Log units by type
            units_by_type = {}
            for unit in units:
                unit_type = unit["type"]
                units_by_type[unit_type] = units_by_type.get(unit_type, 0) + 1
            
            logger.info(f"Units by type: {units_by_type}")
            
            return units
            
        except Exception as e:
            logger.error(f"Error in partition_into_units: {e}")
            return []
    
    def calculate_metrics(self, 
                         core: Polygon,
                         corridors: List[Polygon],
                         units: List[Dict]) -> Dict:
        """Calculate floor plan metrics."""
        try:
            total_area = self.boundary.area
            core_area = core.area if core else 0
            corridor_area = sum(c.area for c in corridors)
            units_area = sum(u["area"] for u in units)
            
            metrics = {
                "total_area": total_area,
                "usable_area": self.usable_area.area,
                "core_area": core_area,
                "corridor_area": corridor_area,
                "units_area": units_area,
                "efficiency": units_area / total_area if total_area > 0 else 0,
                "corridor_ratio": corridor_area / total_area if total_area > 0 else 0,
                "units_count": len(units)
            }
            
            logger.info(f"Metrics: efficiency = {metrics['efficiency']:.2%}, corridor_ratio = {metrics['corridor_ratio']:.2%}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")
            return {}
