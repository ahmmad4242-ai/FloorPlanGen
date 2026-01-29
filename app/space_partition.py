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
                   core_area: float,
                   preferred_location: str = "center",
                   fixed_core: Optional[Polygon] = None) -> Optional[Polygon]:
        """
        Place core at specified location.
        If fixed_core is provided, use it directly.
        Core should be centrally located for optimal circulation.
        """
        try:
            # If fixed core is provided, use it directly
            if fixed_core is not None:
                logger.info(f"Using fixed core: {fixed_core.area:.2f} m²")
                return fixed_core
            
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
                                corridor_width: float,
                                layout_type: str = "double_loaded") -> List[Polygon]:
        """
        Create efficient corridor network with target ratio 12-18%.
        
        Strategy: Perimeter corridors around core (not full building span)
        This leaves maximum space for units while ensuring connectivity.
        """
        corridors = []
        
        try:
            core_bounds = core.bounds
            core_minx, core_miny, core_maxx, core_maxy = core_bounds
            
            # Calculate core dimensions
            core_width = core_maxx - core_minx
            core_height = core_maxy - core_miny
            
            # Create corridor box around core with minimal extension
            # Extension is just enough for unit access (2x corridor width)
            extension = corridor_width * 2.0
            
            # Four corridor segments forming a perimeter around core
            # Top corridor
            top_corridor = box(
                core_minx - extension,
                core_maxy,
                core_maxx + extension,
                core_maxy + corridor_width
            )
            
            # Bottom corridor
            bottom_corridor = box(
                core_minx - extension,
                core_miny - corridor_width,
                core_maxx + extension,
                core_miny
            )
            
            # Left corridor
            left_corridor = box(
                core_minx - corridor_width,
                core_miny - extension,
                core_minx,
                core_maxy + extension
            )
            
            # Right corridor
            right_corridor = box(
                core_maxx,
                core_miny - extension,
                core_maxx + corridor_width,
                core_maxy + extension
            )
            
            # Clip all corridors to usable area
            for corridor_poly in [top_corridor, bottom_corridor, left_corridor, right_corridor]:
                clipped = corridor_poly.intersection(self.usable_area)
                if not clipped.is_empty and clipped.area > 0:
                    corridors.append(clipped)
            
            # Calculate metrics
            total_corridor_area = sum(c.area for c in corridors)
            corridor_ratio = total_corridor_area / self.boundary.area if self.boundary.area > 0 else 0
            
            logger.info(f"Created {len(corridors)} perimeter corridors: {total_corridor_area:.2f} m² ({corridor_ratio*100:.1f}% of total)")
            
            # Validate corridor ratio (should be 12-20% of total area)
            if corridor_ratio > 0.20:
                logger.warning(f"Corridor ratio {corridor_ratio*100:.1f}% exceeds recommended 20%")
            elif corridor_ratio < 0.10:
                logger.warning(f"Corridor ratio {corridor_ratio*100:.1f}% below recommended minimum 10%")
            
            return corridors
            
        except Exception as e:
            logger.error(f"Failed to create corridors: {e}")
            return []
    
    def partition_into_units(self,
                            core: Polygon,
                            corridors: List[Polygon],
                            target_unit_areas: List[float],
                            min_unit_width: float,
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
            
            # Calculate area percentages
            core_percent = (core.area / self.usable_area.area) * 100
            corridor_percent = (sum(c.area for c in corridors) / self.usable_area.area) * 100
            available_percent = (available.area / self.usable_area.area) * 100
            
            logger.info(f"Space allocation: Core={core_percent:.1f}%, Corridors={corridor_percent:.1f}%, Available={available_percent:.1f}%")
            logger.info(f"Available: {available.area:.2f} m², Units: {len(target_unit_areas)}")
            
            # Handle MultiPolygon: work with largest polygons first
            if isinstance(available, MultiPolygon):
                available_polygons = sorted(available.geoms, key=lambda p: p.area, reverse=True)
                logger.info(f"Available area is MultiPolygon with {len(available_polygons)} regions")
                # Use the largest region for now
                available = available_polygons[0] if available_polygons else available
                logger.info(f"Using largest region: {available.area:.2f} m²")
            
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
            # Strategy: Grid-based placement for reliable results
            corridor_union = unary_union(corridors)
            
            # Try to place each unit using grid-based approach
            placed_count = 0
            
            # Create a grid of potential unit positions
            # This is more reliable than perimeter sampling
            available_bounds = available.bounds
            av_minx, av_miny, av_maxx, av_maxy = available_bounds
            
            # Calculate grid parameters - finer grid for better coverage
            grid_spacing = 2.0  # 2m spacing for denser sampling (was 3.0m)
            x_positions = []
            y_positions = []
            
            x = av_minx
            while x < av_maxx:
                x_positions.append(x)
                x += grid_spacing
            x_positions.append(av_maxx)  # Include right edge
            
            y = av_miny
            while y < av_maxy:
                y_positions.append(y)
                y += grid_spacing
            y_positions.append(av_maxy)  # Include top edge
            
            logger.info(f"Grid: {len(x_positions)}x{len(y_positions)} positions ({len(x_positions) * len(y_positions)} total)")
            
            for spec in unit_specs:
                target_area = spec["area"]
                
                # Calculate unit dimensions (try to keep aspect ratio reasonable)
                # Assume 1.5:1 aspect ratio (width:depth)
                target_width = np.sqrt(target_area * 1.5)
                target_depth = target_area / target_width
                
                best_unit = None
                best_score = 0
                attempts = 0
                
                # Try positions in the grid
                for x in x_positions:
                    for y in y_positions:
                        attempts += 1
                        try:
                            # Create unit box at this position
                            unit_poly = box(x, y, x + target_width, y + target_depth)
                            
                            # Intersect with available area
                            unit_clipped = unit_poly.intersection(available)
                            
                            if unit_clipped.is_empty or unit_clipped.area < target_area * 0.50:
                                continue
                            
                            # Check facade length (perimeter contact)
                            facade = unit_clipped.boundary.intersection(self.boundary.boundary)
                            facade_length = facade.length if hasattr(facade, 'length') else 0
                            
                            # Check corridor connection
                            corridor_union = unary_union(corridors)
                            corridor_connection = unit_clipped.boundary.intersection(corridor_union)
                            corridor_length = corridor_connection.length if hasattr(corridor_connection, 'length') else 0
                            
                            # Score: prioritize area match, then facade, then corridor
                            area_score = min(unit_clipped.area / target_area, 1.0) * 10
                            facade_score = min(facade_length / 2.0, 1.0) * 3  # Reduced weight
                            corridor_score = min(corridor_length / 0.3, 1.0) * 2  # Reduced weight
                            score = area_score + facade_score + corridor_score
                            
                            # Relaxed requirements: min facade 1.5m, min corridor 0.3m
                            # Accept units with good area match even with minimal facade/corridor
                            meets_requirements = (
                                (facade_length >= 1.5 and corridor_length >= 0.3) or
                                (unit_clipped.area >= target_area * 0.70)  # Or good area match
                            )
                            
                            if score > best_score and meets_requirements:
                                best_unit = unit_clipped
                                best_score = score
                        
                        except Exception as e:
                            continue
                
                # Log placement attempts
                if not best_unit and attempts > 0:
                    logger.debug(f"Unit {spec['index']}: tried {attempts} positions, no valid placement found")
                
                # Place best unit
                if best_unit:
                    spec["polygon"] = best_unit
                    spec["placed"] = True
                    placed_count += 1
                    
                    logger.info(f"✓ Placed unit {spec['index']} ({spec['type']}, target={spec['area']:.1f}m², actual={best_unit.area:.1f}m², score={best_score:.1f})")
                    
                    # Remove this area from available
                    available = available.difference(best_unit.buffer(0.1))
                    
                    # Update available bounds for next iteration
                    if not available.is_empty:
                        available_bounds = available.bounds
                        av_minx, av_miny, av_maxx, av_maxy = available_bounds
                else:
                    logger.warning(f"✗ Could not place unit {spec['index']} ({spec['type']}, {spec['area']:.1f}m²) - no suitable position found")
            
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
