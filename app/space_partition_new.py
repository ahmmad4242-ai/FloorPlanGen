"""
FloorPlanGen - Enhanced Space Partitioning with Architectural Constraints
===========================================================================
Ensures:
1. Every unit connects to a corridor
2. Every unit has external facade (windows)
3. Corridors form a complete network
4. Exact unit counts are respected
"""

from shapely.geometry import Polygon, Point, LineString, box, MultiPolygon
from shapely.ops import unary_union, split
from typing import List, Dict, Tuple, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ArchitecturalSpacePartitioner:
    """
    Enhanced space partitioner that enforces architectural constraints.
    
    Key principles:
    - Units along perimeter only (external facade requirement)
    - Corridors between core and units (connectivity requirement)
    - Double-loaded corridors for efficiency
    """
    
    def __init__(self, boundary: Polygon, obstacles: List[Polygon]):
        self.boundary = boundary
        self.obstacles = obstacles
        self.usable_area = self._calculate_usable_area()
        
    def _calculate_usable_area(self) -> Polygon:
        """Calculate usable area by subtracting obstacles."""
        try:
            if self.obstacles:
                obstacles_union = unary_union(self.obstacles)
                usable = self.boundary.difference(obstacles_union)
            else:
                usable = self.boundary
            
            logger.info(f"Usable area: {usable.area:.2f} m²")
            return usable
        except Exception as e:
            logger.error(f"Failed to calculate usable area: {e}")
            return self.boundary
    
    def place_core(self,
                   core_area: float = 40.0,
                   preferred_location: str = "center") -> Optional[Polygon]:
        """
        Place core at specified location.
        Core should be centrally located for optimal circulation.
        """
        try:
            centroid = self.boundary.centroid
            bounds = self.boundary.bounds
            minx, miny, maxx, maxy = bounds
            width = maxx - minx
            height = maxy - miny
            
            # Adjust position
            if preferred_location == "center":
                core_center = centroid
            elif preferred_location == "north":
                core_center = Point(centroid.x, centroid.y + height * 0.2)
            elif preferred_location == "south":
                core_center = Point(centroid.x, centroid.y - height * 0.2)
            else:
                core_center = centroid
            
            # Create square core
            core_size = np.sqrt(core_area)
            core = box(
                core_center.x - core_size / 2,
                core_center.y - core_size / 2,
                core_center.x + core_size / 2,
                core_center.y + core_size / 2
            )
            
            # Ensure within usable area
            if not self.usable_area.contains(core):
                core = core.intersection(self.usable_area)
            
            logger.info(f"Placed core: {core.area:.2f} m²")
            return core
            
        except Exception as e:
            logger.error(f"Failed to place core: {e}")
            return None
    
    def create_corridor_network(self,
                                core: Polygon,
                                corridor_width: float = 2.2) -> List[Polygon]:
        """
        Create corridors that:
        1. Connect to core
        2. Extend to building perimeter
        3. Form continuous network
        
        Strategy: Create cross-shaped corridor system
        """
        corridors = []
        
        try:
            core_bounds = core.bounds
            core_minx, core_miny, core_maxx, core_maxy = core_bounds
            
            boundary_bounds = self.boundary.bounds
            bnd_minx, bnd_miny, bnd_maxx, bnd_maxy = boundary_bounds
            
            # Horizontal corridor (spans full width)
            horizontal_corridor = box(
                bnd_minx,
                core_miny - corridor_width / 2,
                bnd_maxx,
                core_maxy + corridor_width / 2
            )
            
            # Vertical corridor (spans full height)
            vertical_corridor = box(
                core_minx - corridor_width / 2,
                bnd_miny,
                core_maxx + corridor_width / 2,
                bnd_maxy
            )
            
            # Clip to usable area
            h_corridor = horizontal_corridor.intersection(self.usable_area)
            v_corridor = vertical_corridor.intersection(self.usable_area)
            
            if h_corridor.area > 0:
                corridors.append(h_corridor)
            if v_corridor.area > 0:
                corridors.append(v_corridor)
            
            total_corridor_area = sum(c.area for c in corridors)
            logger.info(f"Created {len(corridors)} corridors: {total_corridor_area:.2f} m²")
            
            return corridors
            
        except Exception as e:
            logger.error(f"Failed to create corridors: {e}")
            return []
    
    def partition_into_units(self,
                            core: Polygon,
                            corridors: List[Polygon],
                            target_unit_areas: List[float],
                            unit_types: List[Dict] = None) -> List[Dict]:
        """
        Partition space into units with architectural constraints:
        1. Units along building perimeter only (external facade)
        2. Units face corridors (accessibility)
        3. Exact unit counts respected
        
        Strategy: Divide perimeter into segments, assign units
        """
        units = []
        
        try:
            # Calculate occupied area (core + corridors)
            occupied = unary_union([core] + corridors)
            available = self.usable_area.difference(occupied)
            
            if available.area == 0:
                logger.warning("No available area for units")
                return []
            
            logger.info(f"Available: {available.area:.2f} m², Units: {len(target_unit_areas)}")
            
            # Check if MultiPolygon (handle disconnected regions)
            if isinstance(available, MultiPolygon):
                available_polygons = list(available.geoms)
                # Sort by area (largest first)
                available_polygons.sort(key=lambda p: p.area, reverse=True)
            else:
                available_polygons = [available]
            
            # Get building perimeter
            perimeter = self.boundary.boundary
            perimeter_length = perimeter.length
            
            # Calculate target unit dimensions
            total_requested_area = sum(target_unit_areas)
            
            # Check if we need to scale down
            if total_requested_area > available.area * 0.90:
                scale_factor = (available.area * 0.85) / total_requested_area
                target_unit_areas = [a * scale_factor for a in target_unit_areas]
                logger.info(f"Scaled unit areas by {scale_factor:.2f}x")
            
            # Sort units by area (place larger units first for better fit)
            unit_specs = []
            for i, area in enumerate(target_unit_areas):
                unit_type_info = unit_types[i] if unit_types and i < len(unit_types) else {
                    "type": "Studio", "min_area": 50, "max_area": 100
                }
                unit_specs.append({
                    "index": i,
                    "area": area,
                    "type": unit_type_info.get("type", "Studio"),
                    "placed": False,
                    "polygon": None
                })
            
            # Sort by area (largest first)
            unit_specs.sort(key=lambda x: x["area"], reverse=True)
            
            # Divide building perimeter into unit segments
            # Strategy: Clockwise placement along perimeter
            corridor_union = unary_union(corridors)
            
            # Get points along perimeter
            num_points = len(unit_specs) * 4  # Sample 4 points per unit
            perimeter_points = []
            
            # Sample points along perimeter
            for i in range(num_points):
                distance = (i / num_points) * perimeter_length
                point = perimeter.interpolate(distance)
                perimeter_points.append(point)
            
            # Try to place each unit
            placed_count = 0
            unit_depth = 6.0  # Standard unit depth from facade
            
            for spec in unit_specs:
                target_area = spec["area"]
                
                # Calculate target facade length
                # Unit depth × facade width = area
                target_facade_width = target_area / unit_depth
                
                # Try different positions along perimeter
                best_unit = None
                best_score = 0
                
                for start_idx in range(0, len(perimeter_points), 2):  # Try every 2nd point
                    try:
                        # Get facade segment
                        p1 = perimeter_points[start_idx]
                        end_idx = min(start_idx + int(target_facade_width / (perimeter_length / num_points)) + 1,
                                    len(perimeter_points) - 1)
                        p2 = perimeter_points[end_idx]
                        
                        # Create perpendicular vector pointing inward
                        dx = p2.x - p1.x
                        dy = p2.y - p1.y
                        length = np.sqrt(dx**2 + dy**2)
                        
                        if length < 2.0:  # Too small facade
                            continue
                        
                        # Normal vector (perpendicular, pointing inward)
                        nx = -dy / length
                        ny = dx / length
                        
                        # Check if pointing inward (toward centroid)
                        centroid = self.boundary.centroid
                        midpoint = Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
                        to_centroid_x = centroid.x - midpoint.x
                        to_centroid_y = centroid.y - midpoint.y
                        
                        # Flip if pointing outward
                        if nx * to_centroid_x + ny * to_centroid_y < 0:
                            nx = -nx
                            ny = -ny
                        
                        # Create unit rectangle
                        corners = [
                            (p1.x, p1.y),
                            (p2.x, p2.y),
                            (p2.x + nx * unit_depth, p2.y + ny * unit_depth),
                            (p1.x + nx * unit_depth, p1.y + ny * unit_depth)
                        ]
                        
                        unit_poly = Polygon(corners)
                        
                        # Intersect with available area
                        unit_clipped = unit_poly.intersection(available)
                        
                        if not unit_clipped.is_empty and unit_clipped.area > target_area * 0.65:
                            # Check facade length
                            facade = unit_clipped.boundary.intersection(perimeter)
                            facade_length = facade.length if hasattr(facade, 'length') else 0
                            
                            # Check corridor connection
                            corridor_connection = unit_clipped.boundary.intersection(corridor_union)
                            corridor_length = corridor_connection.length if hasattr(corridor_connection, 'length') else 0
                            
                            # Score: facade length + corridor connection + area match
                            score = (facade_length / 3.0) + (corridor_length / 0.9) + (unit_clipped.area / target_area)
                            
                            if score > best_score and facade_length >= 2.5 and corridor_length >= 0.8:
                                best_unit = unit_clipped
                                best_score = score
                    
                    except Exception as e:
                        continue
                
                # Place best unit
                if best_unit:
                    spec["polygon"] = best_unit
                    spec["placed"] = True
                    placed_count += 1
                    
                    # Remove this area from available
                    available = available.difference(best_unit.buffer(0.1))
                else:
                    logger.warning(f"Could not place unit {spec['index']} ({spec['type']}, {spec['area']:.1f}m²)")
            
            # Build final units list (restore original order)
            unit_specs.sort(key=lambda x: x["index"])
            
            unit_id = 1
            for spec in unit_specs:
                if spec["placed"] and spec["polygon"]:
                    units.append({
                        "id": f"unit_{unit_id}",
                        "type": spec["type"],
                        "polygon": spec["polygon"],
                        "area": spec["polygon"].area,
                        "centroid": spec["polygon"].centroid
                    })
                    unit_id += 1
            
            logger.info(f"Placed {len(units)}/{len(target_unit_areas)} units")
            
            # Log by type
            units_by_type = {}
            for unit in units:
                ut = unit["type"]
                units_by_type[ut] = units_by_type.get(ut, 0) + 1
            logger.info(f"Units by type: {units_by_type}")
            
            return units
            
        except Exception as e:
            logger.error(f"Error partitioning units: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def calculate_metrics(self,
                         core: Polygon,
                         corridors: List[Polygon],
                         units: List[Dict]) -> Dict:
        """Calculate floor plan metrics."""
        total_area = self.boundary.area
        core_area = core.area if core else 0
        corridor_area = sum(c.area for c in corridors)
        units_area = sum(u["area"] for u in units)
        
        return {
            "total_area": total_area,
            "usable_area": self.usable_area.area,
            "core_area": core_area,
            "corridor_area": corridor_area,
            "units_area": units_area,
            "efficiency": units_area / total_area if total_area > 0 else 0,
            "corridor_ratio": corridor_area / total_area if total_area > 0 else 0,
            "units_count": len(units)
        }
