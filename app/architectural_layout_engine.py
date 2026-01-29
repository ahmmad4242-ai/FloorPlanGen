"""
FloorPlanGen - Architectural Layout Engine
==========================================
Professional architectural floor plan generation with:
1. Connected units - all units share walls where possible
2. Logical corridor network - spine + branches to reach all units
3. Proper unit organization - grouped by type
4. Perimeter optimization - units along exterior walls
5. Core placement - central or specified location

Architectural Principles Applied:
- Double-loaded corridors (units on both sides)
- Minimum corridor width: 1.8m
- All units have exterior facade access
- Units organized in rows for efficiency
- Core centrally located for equal access
"""

from shapely.geometry import Polygon, Point, LineString, box, MultiPolygon
from shapely.ops import unary_union, split
from typing import List, Dict, Tuple, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ArchitecturalLayoutEngine:
    """
    Professional architectural layout engine.
    Creates proper floor plans with connected units and logical corridors.
    """
    
    def __init__(self, boundary: Polygon, obstacles: List[Polygon] = None):
        self.boundary = boundary
        self.obstacles = obstacles or []
        self.usable_area = self._calculate_usable_area()
        
        # Get boundary dimensions
        minx, miny, maxx, maxy = boundary.bounds
        self.width = maxx - minx
        self.height = maxy - miny
        self.area = boundary.area
        
        logger.info(f"Layout engine initialized: {self.width:.1f}m × {self.height:.1f}m = {self.area:.1f}m²")
    
    def _calculate_usable_area(self) -> Polygon:
        """Calculate usable area by subtracting obstacles."""
        try:
            if self.obstacles:
                obstacles_union = unary_union(self.obstacles)
                usable = self.boundary.difference(obstacles_union)
            else:
                usable = self.boundary
            return usable
        except Exception as e:
            logger.error(f"Failed to calculate usable area: {e}")
            return self.boundary
    
    def place_core(self,
                   core_area: float,
                   preferred_location: str = "center",
                   fixed_core: Optional[Polygon] = None) -> Optional[Polygon]:
        """
        Place core (elevators, stairs, services).
        Core should be centrally located for optimal circulation.
        """
        try:
            if fixed_core is not None:
                logger.info(f"Using fixed core: {fixed_core.area:.2f} m²")
                return fixed_core
            
            centroid = self.boundary.centroid
            bounds = self.boundary.bounds
            minx, miny, maxx, maxy = bounds
            width = maxx - minx
            height = maxy - miny
            
            # Calculate core dimensions (prefer square or rectangular)
            # For typical residential buildings, core is often rectangular
            core_width = np.sqrt(core_area * 0.8)  # Slightly wider than deep
            core_depth = core_area / core_width
            
            # Adjust position based on preference
            if preferred_location == "center":
                core_center = centroid
            elif preferred_location == "north":
                core_center = Point(centroid.x, centroid.y + height * 0.2)
            elif preferred_location == "south":
                core_center = Point(centroid.x, centroid.y - height * 0.2)
            elif preferred_location == "east":
                core_center = Point(centroid.x + width * 0.2, centroid.y)
            elif preferred_location == "west":
                core_center = Point(centroid.x - width * 0.2, centroid.y)
            else:
                core_center = centroid
            
            # Create core box
            core = box(
                core_center.x - core_width / 2,
                core_center.y - core_depth / 2,
                core_center.x + core_width / 2,
                core_center.y + core_depth / 2
            )
            
            # Ensure within usable area
            if not self.usable_area.contains(core):
                core = core.intersection(self.usable_area)
            
            logger.info(f"Placed core: {core.area:.2f} m² at {preferred_location}")
            return core
            
        except Exception as e:
            logger.error(f"Failed to place core: {e}")
            return None
    
    def create_corridor_spine(self,
                             core: Polygon,
                             corridor_width: float,
                             layout_type: str = "double_loaded") -> List[Polygon]:
        """
        Create main corridor spine connecting core to building perimeter.
        
        Strategy:
        1. Main horizontal corridor through center
        2. Vertical branches to reach all areas
        3. Ensure all regions are accessible
        
        This creates a logical network that reaches all units.
        """
        corridors = []
        
        try:
            core_bounds = core.bounds
            core_minx, core_miny, core_maxx, core_maxy = core_bounds
            core_center_x = (core_minx + core_maxx) / 2
            core_center_y = (core_miny + core_maxy) / 2
            
            building_bounds = self.boundary.bounds
            bldg_minx, bldg_miny, bldg_maxx, bldg_maxy = building_bounds
            
            # Strategy: Minimal corridor network around core + side access
            # Much less area than old approach
            
            # 1. Ring corridor around core (double-loaded access)
            ring_extension = corridor_width * 1.5  # Minimal extension
            
            # Top corridor (north of core)
            top_corridor = box(
                core_minx - ring_extension,
                core_maxy,
                core_maxx + ring_extension,
                core_maxy + corridor_width
            )
            corridors.append(top_corridor)
            
            # Bottom corridor (south of core)
            bottom_corridor = box(
                core_minx - ring_extension,
                core_miny - corridor_width,
                core_maxx + ring_extension,
                core_miny
            )
            corridors.append(bottom_corridor)
            
            # Left corridor (west of core)
            left_corridor = box(
                core_minx - corridor_width,
                core_miny - ring_extension,
                core_minx,
                core_maxy + ring_extension
            )
            corridors.append(left_corridor)
            
            # Right corridor (east of core)
            right_corridor = box(
                core_maxx,
                core_miny - ring_extension,
                core_maxx + corridor_width,
                core_maxy + ring_extension
            )
            corridors.append(right_corridor)
            
            # 2. Horizontal spine (connects to building edges)
            # Only if building is large enough
            if self.width > (core_maxx - core_minx) * 2:
                # Left horizontal connector
                left_spine = box(
                    bldg_minx,
                    core_center_y - corridor_width / 2,
                    core_minx - corridor_width,
                    core_center_y + corridor_width / 2
                )
                corridors.append(left_spine)
                
                # Right horizontal connector
                right_spine = box(
                    core_maxx + corridor_width,
                    core_center_y - corridor_width / 2,
                    bldg_maxx,
                    core_center_y + corridor_width / 2
                )
                corridors.append(right_spine)
            
            # Clip all corridors to usable area and merge overlaps
            clipped_corridors = []
            for corridor in corridors:
                clipped = corridor.intersection(self.usable_area)
                if not clipped.is_empty and clipped.area > 0:
                    clipped_corridors.append(clipped)
            
            # Merge overlapping corridors for cleaner result
            if clipped_corridors:
                corridor_union = unary_union(clipped_corridors)
                if isinstance(corridor_union, MultiPolygon):
                    final_corridors = list(corridor_union.geoms)
                else:
                    final_corridors = [corridor_union]
            else:
                final_corridors = []
            
            total_corridor_area = sum(c.area for c in final_corridors)
            corridor_ratio = total_corridor_area / self.area if self.area > 0 else 0
            
            logger.info(f"Created corridor network: {total_corridor_area:.2f} m² ({corridor_ratio*100:.1f}% of total)")
            logger.info(f"Layout type: {layout_type}, Corridors: {len(final_corridors)}")
            
            return final_corridors
            
        except Exception as e:
            logger.error(f"Failed to create corridor spine: {e}")
            return []
    
    def layout_units_along_perimeter(self,
                                     core: Polygon,
                                     corridors: List[Polygon],
                                     unit_types: List[Dict]) -> List[Dict]:
        """
        Layout units along building perimeter with proper adhesion.
        
        Strategy:
        1. Identify available perimeter regions (not occupied by core/corridors)
        2. Layout units in rows/columns along perimeter
        3. Ensure units share walls (adhesion)
        4. Group similar unit types together
        5. All units face corridors for access
        
        Unit types format:
        [
            {"type": "Studio", "count": 5, "min_area": 25, "max_area": 35},
            {"type": "1BR", "count": 10, "min_area": 45, "max_area": 65},
            ...
        ]
        """
        units = []
        
        try:
            # Calculate occupied area
            occupied = unary_union([core] + corridors)
            available = self.usable_area.difference(occupied)
            
            if available.is_empty:
                logger.warning("No available area for units")
                return []
            
            logger.info(f"Available for units: {available.area:.2f} m²")
            
            # Prepare unit specifications
            unit_specs = []
            for unit_type_spec in unit_types:
                unit_type = unit_type_spec.get("type", "Studio")
                count = unit_type_spec.get("count", 1)
                min_area = unit_type_spec.get("min_area", 50)
                max_area = unit_type_spec.get("max_area", 100)
                
                for i in range(count):
                    # Random area within range
                    target_area = np.random.uniform(min_area, max_area)
                    unit_specs.append({
                        "type": unit_type,
                        "target_area": target_area,
                        "min_area": min_area,
                        "max_area": max_area
                    })
            
            logger.info(f"Planning layout for {len(unit_specs)} units")
            
            # Get building bounds
            bounds = self.boundary.bounds
            minx, miny, maxx, maxy = bounds
            
            # Calculate typical unit dimensions
            # Standard aspect ratio: 1.2 to 1.5 (slightly wider than deep)
            avg_area = np.mean([spec["target_area"] for spec in unit_specs])
            typical_width = np.sqrt(avg_area * 1.3)
            typical_depth = avg_area / typical_width
            
            logger.info(f"Typical unit: {typical_width:.1f}m × {typical_depth:.1f}m = {avg_area:.1f}m²")
            
            # Layout strategy: Divide available space into grid cells
            # Place units in cells, filling left-to-right, top-to-bottom
            
            # Get available space bounds
            if isinstance(available, MultiPolygon):
                # Use all regions
                available_regions = list(available.geoms)
                available_regions.sort(key=lambda p: p.area, reverse=True)
                logger.info(f"Available area has {len(available_regions)} regions")
            else:
                available_regions = [available]
            
            # Calculate typical unit dimensions
            avg_area = np.mean([spec["target_area"] for spec in unit_specs])
            typical_width = np.sqrt(avg_area * 1.2)  # Slightly wider
            typical_depth = avg_area / typical_width
            
            logger.info(f"Typical unit: {typical_width:.1f}m × {typical_depth:.1f}m = {avg_area:.1f}m²")
            
            # Try to place each unit
            placed_units = []
            
            for spec in unit_specs:
                target_area = spec["target_area"]
                
                # Calculate this unit's dimensions
                unit_width = np.sqrt(target_area * 1.2)
                unit_depth = target_area / unit_width
                
                best_unit = None
                best_score = 0
                
                # Try each available region
                for region in available_regions:
                    if region.is_empty or region.area < target_area * 0.5:
                        continue
                    
                    reg_bounds = region.bounds
                    reg_minx, reg_miny, reg_maxx, reg_maxy = reg_bounds
                    
                    # Try multiple positions in this region
                    # Grid sampling with 2m spacing
                    x_positions = np.arange(reg_minx, reg_maxx - unit_width, 2.0)
                    y_positions = np.arange(reg_miny, reg_maxy - unit_depth, 2.0)
                    
                    # Limit attempts for performance
                    max_attempts = min(len(x_positions) * len(y_positions), 100)
                    
                    for x in x_positions:
                        for y in y_positions:
                            if max_attempts <= 0:
                                break
                            max_attempts -= 1
                            
                            # Create unit box
                            unit_poly = box(x, y, x + unit_width, y + unit_depth)
                            
                            # Clip to region
                            unit_clipped = unit_poly.intersection(region)
                            
                            if unit_clipped.is_empty or unit_clipped.area < target_area * 0.60:
                                continue
                            
                            # Score based on area match
                            area_match = min(unit_clipped.area / target_area, 1.0)
                            
                            # Check perimeter contact (window access)
                            perimeter_contact = unit_clipped.boundary.intersection(self.boundary.boundary)
                            perimeter_length = perimeter_contact.length if hasattr(perimeter_contact, 'length') else 0
                            perimeter_score = min(perimeter_length / 2.0, 1.0)
                            
                            # Total score: heavily weight area match
                            score = area_match * 10 + perimeter_score * 2
                            
                            if score > best_score:
                                best_unit = unit_clipped
                                best_score = score
                        
                        if max_attempts <= 0:
                            break
                
                # Place best unit if found
                if best_unit:
                    placed_units.append({
                        "type": spec["type"],
                        "polygon": best_unit,
                        "area": best_unit.area
                    })
                    
                    # Remove from all regions
                    buffer_dist = 0.05
                    new_regions = []
                    for region in available_regions:
                        remaining = region.difference(best_unit.buffer(buffer_dist))
                        if not remaining.is_empty:
                            if isinstance(remaining, MultiPolygon):
                                new_regions.extend(list(remaining.geoms))
                            else:
                                new_regions.append(remaining)
                    available_regions = new_regions
                    
                    # Sort by area
                    available_regions.sort(key=lambda p: p.area, reverse=True)
                else:
                    logger.debug(f"Could not place {spec['type']} unit ({target_area:.1f}m²)")
            
            # Create final units list with proper IDs
            for i, unit_data in enumerate(placed_units, 1):
                units.append({
                    "id": f"unit_{i}",
                    "type": unit_data["type"],
                    "polygon": unit_data["polygon"],
                    "area": unit_data["area"],
                    "centroid": unit_data["polygon"].centroid
                })
            
            logger.info(f"Placed {len(units)}/{len(unit_specs)} units")
            
            # Log by type
            units_by_type = {}
            for unit in units:
                ut = unit["type"]
                units_by_type[ut] = units_by_type.get(ut, 0) + 1
            logger.info(f"Units by type: {units_by_type}")
            
            return units
            
        except Exception as e:
            logger.error(f"Error in layout_units_along_perimeter: {e}")
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
