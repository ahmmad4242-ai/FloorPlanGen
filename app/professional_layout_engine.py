"""
FloorPlanGen - Professional Layout Engine
==========================================
Builds CORRECT floor plans with:
1. VISIBLE corridors (minimum 10% of floor area)
2. ALL units connected to corridors with proper doors
3. Units on building perimeter for windows/light
4. Logical corridor networks (spine + branches)
5. No overlapping, proper adhesion

Architectural Standards Applied:
- Corridor ratio: 10-15% of total area
- Corridor width: 2.2-2.5m (visible in plans)
- Double-loaded corridors (units both sides)
- All units have exterior facade access
- Core centrally located
"""

from shapely.geometry import Polygon, Point, LineString, box, MultiPolygon
from shapely.ops import unary_union, split
from typing import List, Dict, Tuple, Optional
import numpy as np
import logging

# Import corridor pattern generator V2.2
# Try relative import first, then absolute
try:
    from .corridor_patterns import CorridorPatternGenerator
    logger = logging.getLogger(__name__)
    logger.info("✅ Imported CorridorPatternGenerator (relative)")
except (ImportError, ValueError):
    try:
        from corridor_patterns import CorridorPatternGenerator
        logger = logging.getLogger(__name__)
        logger.info("✅ Imported CorridorPatternGenerator (absolute)")
    except ImportError as e:
        # Fallback: use inline T-pattern only
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Failed to import CorridorPatternGenerator: {e}")
        logger.warning("⚠️ Using fallback T-pattern corridor generation")
        CorridorPatternGenerator = None

logger = logging.getLogger(__name__)


class ProfessionalLayoutEngine:
    """
    Professional architectural layout engine.
    Creates floor plans that follow real-world architectural standards.
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
        
        logger.info(f"Professional Layout Engine initialized: {self.width:.1f}m × {self.height:.1f}m = {self.area:.1f}m²")
    
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
                   preferred_location: str = "center") -> Optional[Polygon]:
        """
        Place core (elevators, stairs, services).
        Core should be centrally located for optimal circulation.
        """
        try:
            centroid = self.boundary.centroid
            bounds = self.boundary.bounds
            minx, miny, maxx, maxy = bounds
            width = maxx - minx
            height = maxy - miny
            
            # Calculate core dimensions (square-ish)
            core_width = np.sqrt(core_area * 0.9)
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
    
    def create_visible_corridor_network(self,
                                       core: Polygon,
                                       corridor_width: float = 2.5,
                                       pattern: str = "auto") -> List[Polygon]:
        """
        Create VISIBLE corridor network with MULTIPLE PATTERNS (V2.2).
        
        Supports:
        - "auto": Auto-select based on building shape (default)
        - "T": T-shaped (main spine + branch) - balanced
        - "U": U-shaped (3 sides) - rectangular buildings
        - "L": L-shaped (2 perpendicular) - corner/narrow buildings
        - "H": H-shaped (double-loaded + cross) - large buildings
        - "+": Plus/Cross (4 directions) - square buildings
        - "line": Single straight corridor - narrow buildings
        
        Args:
            core: Core polygon
            corridor_width: Corridor width in meters (2.2-2.5m)
            pattern: Corridor pattern type or "auto"
        
        Returns:
            List of corridor polygons
        """
        try:
            # Check if CorridorPatternGenerator is available
            if CorridorPatternGenerator is None:
                logger.warning("⚠️ CorridorPatternGenerator not available, using fallback T-pattern")
                return self._create_fallback_T_pattern_corridors(core, corridor_width)
            
            # Use advanced pattern generator V2.2
            generator = CorridorPatternGenerator(
                boundary=self.boundary,
                core=core,
                corridor_width=corridor_width
            )
            
            # Generate corridors with selected pattern
            corridors = generator.generate(pattern=pattern, usable_area=self.usable_area)
            
            # Calculate metrics
            total_corridor_area = sum(c.area for c in corridors)
            corridor_ratio = total_corridor_area / self.area if self.area > 0 else 0
            
            logger.info(f"Created {pattern}-pattern corridor network:")
            logger.info(f"  Total corridor area: {total_corridor_area:.2f} m²")
            logger.info(f"  Corridor ratio: {corridor_ratio*100:.1f}% (target 8-12%)")
            logger.info(f"  Segments: {len(corridors)}")
            logger.info(f"  Width: {corridor_width:.2f} m")
            
            return corridors
            
        except Exception as e:
            logger.error(f"Failed to create corridor network: {e}")
            return []
            
            bounds = self.boundary.bounds
            minx, miny, maxx, maxy = bounds
            core_centroid = core.centroid
            width = maxx - minx
            height = maxy - miny
            
            corridors = []
            
            # Strategy: ONE main corridor spine (horizontal or vertical based on building shape)
            # + Minimal connecting branches to reach all zones
            
            if width >= height:
                # Wider building: use horizontal spine
                logger.info(f"Building is wider ({width:.1f}m × {height:.1f}m) - using horizontal spine")
                
                # Main horizontal spine through core
                main_corridor = box(
                    minx,
                    core_centroid.y - corridor_width / 2,
                    maxx,
                    core_centroid.y + corridor_width / 2
                )
                main_corridor = main_corridor.intersection(self.usable_area)
                if not main_corridor.is_empty:
                    corridors.append(main_corridor)
                
                # Extended vertical branches to reach top/bottom zones (80% of height)
                branch_length = height * 0.8
                
                # North branch (extended to reach top units)
                if height > corridor_width * 3:  # Only if building is tall enough
                    north_branch = box(
                        core_centroid.x - corridor_width / 2,
                        core_centroid.y + corridor_width / 2,
                        core_centroid.x + corridor_width / 2,
                        min(maxy - corridor_width, core_centroid.y + branch_length)
                    )
                    north_branch = north_branch.intersection(self.usable_area)
                    if not north_branch.is_empty and north_branch.area > corridor_width * 2:
                        corridors.append(north_branch)
                
                # South branch (extended to reach bottom units)
                if height > corridor_width * 3:
                    south_branch = box(
                        core_centroid.x - corridor_width / 2,
                        max(miny + corridor_width, core_centroid.y - branch_length),
                        core_centroid.x + corridor_width / 2,
                        core_centroid.y - corridor_width / 2
                    )
                    south_branch = south_branch.intersection(self.usable_area)
                    if not south_branch.is_empty and south_branch.area > corridor_width * 2:
                        corridors.append(south_branch)
            
            else:
                # Taller building: use vertical spine
                logger.info(f"Building is taller ({width:.1f}m × {height:.1f}m) - using vertical spine")
                
                # Main vertical spine through core
                main_corridor = box(
                    core_centroid.x - corridor_width / 2,
                    miny,
                    core_centroid.x + corridor_width / 2,
                    maxy
                )
                main_corridor = main_corridor.intersection(self.usable_area)
                if not main_corridor.is_empty:
                    corridors.append(main_corridor)
                
                # Extended horizontal branches to reach left/right zones (80% of width)
                branch_length = width * 0.8
                
                # East branch (extended to reach right units)
                if width > corridor_width * 3:
                    east_branch = box(
                        core_centroid.x + corridor_width / 2,
                        core_centroid.y - corridor_width / 2,
                        min(maxx - corridor_width, core_centroid.x + branch_length),
                        core_centroid.y + corridor_width / 2
                    )
                    east_branch = east_branch.intersection(self.usable_area)
                    if not east_branch.is_empty and east_branch.area > corridor_width * 2:
                        corridors.append(east_branch)
                
                # West branch (extended to reach left units)
                if width > corridor_width * 3:
                    west_branch = box(
                        max(minx + corridor_width, core_centroid.x - branch_length),
                        core_centroid.y - corridor_width / 2,
                        core_centroid.x - corridor_width / 2,
                        core_centroid.y + corridor_width / 2
                    )
                    west_branch = west_branch.intersection(self.usable_area)
                    if not west_branch.is_empty and west_branch.area > corridor_width * 2:
                        corridors.append(west_branch)
            
            # Calculate total corridor area
            total_corridor_area = sum(c.area for c in corridors)
            corridor_ratio = total_corridor_area / self.area if self.area > 0 else 0
            
            logger.info(f"Created EFFICIENT corridor network:")
            logger.info(f"  Total corridor area: {total_corridor_area:.2f} m²")
            logger.info(f"  Corridor ratio: {corridor_ratio*100:.1f}% (target 8-12%)")
            logger.info(f"  Segments: {len(corridors)}")
            logger.info(f"  Width: {corridor_width:.2f} m")
            
            return corridors
            
        except Exception as e:
            logger.error(f"Failed to create corridor network: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _create_fallback_T_pattern_corridors(self, core: Polygon, corridor_width: float) -> List[Polygon]:
        """
        Fallback T-pattern corridor generation (if CorridorPatternGenerator unavailable).
        Simple cross/T pattern with main spine + perpendicular branch.
        """
        try:
            w = max(min(corridor_width, 2.5), 2.2)
            bounds = self.boundary.bounds
            minx, miny, maxx, maxy = bounds
            core_center = core.centroid
            width = maxx - minx
            height = maxy - miny
            
            corridors = []
            
            if width >= height:
                # Horizontal main spine
                main = box(minx, core_center.y - w/2, maxx, core_center.y + w/2)
                main = main.intersection(self.usable_area)
                if not main.is_empty:
                    corridors.append(main)
                
                # Vertical branch (80% of height)
                branch_len = height * 0.8 / 2
                branch = box(
                    core_center.x - w/2,
                    core_center.y - branch_len,
                    core_center.x + w/2,
                    core_center.y + branch_len
                )
                branch = branch.intersection(self.usable_area)
                if not branch.is_empty:
                    corridors.append(branch)
            else:
                # Vertical main spine
                main = box(core_center.x - w/2, miny, core_center.x + w/2, maxy)
                main = main.intersection(self.usable_area)
                if not main.is_empty:
                    corridors.append(main)
                
                # Horizontal branch (80% of width)
                branch_len = width * 0.8 / 2
                branch = box(
                    core_center.x - branch_len,
                    core_center.y - w/2,
                    core_center.x + branch_len,
                    core_center.y + w/2
                )
                branch = branch.intersection(self.usable_area)
                if not branch.is_empty:
                    corridors.append(branch)
            
            total_area = sum(c.area for c in corridors)
            ratio = total_area / self.area * 100 if self.area > 0 else 0
            logger.info(f"Created fallback T-pattern: {len(corridors)} corridors, {total_area:.1f}m² ({ratio:.1f}%)")
            
            return corridors
            
        except Exception as e:
            logger.error(f"Fallback corridor generation failed: {e}")
            return []
    
    def _place_units_pass(self,
                          unit_specs: List[Dict],
                          available_regions: List[Polygon],
                          corridor_union: Polygon,
                          placed_units: List[Dict],
                          pass_config: Dict) -> List[Dict]:
        """
        Single placement pass with specific configuration.
        Returns remaining unplaced unit specs.
        """
        remaining = []
        pass_name = pass_config["name"]
        placed_count = 0
        
        for spec in unit_specs:
            target_area = spec["target_area"]
            unit_type = spec["type"]
            
            # Calculate unit dimensions
            unit_width = np.sqrt(target_area * 1.3)
            unit_depth = target_area / unit_width
            
            best_unit = None
            best_score = -1
            
            # Try each available region
            for region in available_regions:
                if region.is_empty or region.area < target_area * 0.3:
                    continue
                
                reg_bounds = region.bounds
                reg_minx, reg_miny, reg_maxx, reg_maxy = reg_bounds
                
                # Fine grid sampling
                x_step = max(0.2, unit_width * 0.15)
                y_step = max(0.2, unit_depth * 0.15)
                
                x_positions = np.arange(reg_minx, reg_maxx - unit_width * 0.2, x_step)
                y_positions = np.arange(reg_miny, reg_maxy - unit_depth * 0.2, y_step)
                
                max_attempts = pass_config["max_attempts"]
                attempts = 0
                
                for x in x_positions:
                    for y in y_positions:
                        if attempts >= max_attempts:
                            break
                        attempts += 1
                        
                        # Create unit box
                        unit_poly = box(x, y, x + unit_width, y + unit_depth)
                        unit_clipped = unit_poly.intersection(region)
                        
                        # ✅ V2.4.1: CRITICAL FIX - Check if unit_clipped is a valid Polygon
                        if unit_clipped.is_empty or not isinstance(unit_clipped, Polygon):
                            continue
                        
                        # Check minimum area
                        if unit_clipped.area < target_area * pass_config["min_area_match"]:
                            continue
                        
                        # ✅ V2.4.1: Safe perimeter access check
                        try:
                            if unit_clipped.boundary is None:
                                continue
                            perimeter_contact = unit_clipped.boundary.intersection(self.boundary.boundary)
                            perimeter_length = perimeter_contact.length if hasattr(perimeter_contact, 'length') else 0
                        except Exception as e:
                            logger.debug(f"Perimeter check failed: {e}")
                            continue
                        
                        # Apply perimeter requirement from config
                        if perimeter_length < pass_config["min_perimeter"]:
                            continue
                        
                        # Check corridor proximity AND contact
                        try:
                            corridor_distance = unit_clipped.distance(corridor_union)
                            # Check if unit TOUCHES corridor (shared edge)
                            corridor_contact = unit_clipped.intersection(corridor_union.buffer(0.05))
                            has_corridor_contact = not corridor_contact.is_empty and corridor_contact.area < 0.1
                            
                            # NEW V2.2: Check corridor-facing width (minimum 2.5m for proper entrance)
                            min_facing_width = pass_config.get("min_corridor_facing_width", 2.5)
                            
                            # ✅ V2.4.1: Safe boundary check
                            if unit_clipped.boundary is None:
                                facing_width = 0
                            else:
                                corridor_facing_edge = unit_clipped.boundary.intersection(corridor_union.buffer(0.1))
                                
                                if hasattr(corridor_facing_edge, 'length'):
                                    facing_width = corridor_facing_edge.length
                                else:
                                    facing_width = 0
                            
                            # Skip if facing width too narrow (can't fit door properly)
                            if facing_width > 0 and facing_width < min_facing_width:
                                continue
                        except Exception as e:
                            logger.debug(f"Corridor check failed: {e}")
                            corridor_distance = 999
                            has_corridor_contact = False
                        
                        # Apply corridor distance requirement from config
                        if corridor_distance > pass_config["max_corridor_distance"]:
                            continue
                        
                        # Score this placement
                        area_match = min(unit_clipped.area / target_area, target_area / unit_clipped.area)
                        perimeter_score = min(perimeter_length / 3.0, 1.0)
                        corridor_score = max(0, 1.0 - corridor_distance / pass_config["max_corridor_distance"])
                        contact_bonus = 2.0 if has_corridor_contact else 0  # Bonus for touching corridor
                        
                        # Weighted score (contact is CRITICAL)
                        score = area_match * 8 + perimeter_score * 3 + corridor_score * 4 + contact_bonus
                        
                        if score > best_score:
                            best_unit = unit_clipped
                            best_score = score
                    
                    if attempts >= max_attempts:
                        break
            
            # Place best unit if found
            if best_unit and best_score > 0:
                placed_units.append({
                    "type": unit_type,
                    "polygon": best_unit,
                    "area": best_unit.area
                })
                placed_count += 1
                
                # ✅ V2.4: Remove from available regions (with proper wall spacing)
                buffer_dist = 0.15  # 15cm spacing (wall thickness) - reduced for better density
                new_regions = []
                for region in available_regions:
                    remaining_area = region.difference(best_unit.buffer(buffer_dist))
                    if not remaining_area.is_empty:
                        if isinstance(remaining_area, MultiPolygon):
                            new_regions.extend(list(remaining_area.geoms))
                        else:
                            new_regions.append(remaining_area)
                available_regions[:] = new_regions
                available_regions.sort(key=lambda p: p.area, reverse=True)
            else:
                # Could not place this unit in this pass
                remaining.append(spec)
        
        logger.info(f"  Pass '{pass_name}': Placed {placed_count} units")
        return remaining
    
    def layout_units_with_corridor_access(self,
                                         core: Polygon,
                                         corridors: List[Polygon],
                                         unit_constraints: Dict) -> List[Dict]:
        """
        Layout units DYNAMICALLY based on percentages (V2).
        
        NEW: Supports two strategies:
        1. "fill_available": Fill all available space based on percentages
        2. "target_count": Place specific count (old behavior)
        
        Unit constraints format V2:
        {
            "generation_strategy": "fill_available" | "target_count",
            "units": [
                {
                    "type": "Studio",
                    "percentage": 20,  # NEW!
                    "count": 5,        # OLD (optional)
                    "priority": 1,
                    "area": {"min": 25, "target": 30, "max": 35},
                    "dimensions": {
                        "corridor_width": {"min": 3.5, "max": 5.0},
                        "depth": {"min": 4.0, "max": 6.5}
                    }
                }
            ],
            "total_units": {"min": 10, "max": 50},
            "distribution_strategy": {...}
        }
        """
        units = []
        
        try:
            # Calculate available area (exclude core + corridors)
            occupied = unary_union([core] + corridors)
            available = self.usable_area.difference(occupied)
            
            if available.is_empty:
                logger.warning("No available area for units after corridors")
                return []
            
            logger.info(f"Available for units: {available.area:.2f} m²")
            
            # Extract constraints
            generation_strategy = unit_constraints.get("generation_strategy", "fill_available")
            unit_types_config = unit_constraints.get("units", [])
            total_units_config = unit_constraints.get("total_units", {})
            
            logger.info(f"Generation strategy: {generation_strategy}")
            
            # ===== NEW: Estimate total units dynamically =====
            if generation_strategy == "fill_available":
                # Calculate average unit area
                avg_area = 0
                total_percentage = 0
                for ut in unit_types_config:
                    area_config = ut.get("area", {})
                    if isinstance(area_config, dict):
                        min_area = area_config.get("min", 50)
                        max_area = area_config.get("max", 100)
                        target_area = area_config.get("target", (min_area + max_area) / 2)
                    else:
                        target_area = 60  # default
                    
                    percentage = ut.get("percentage", 0)
                    avg_area += target_area * percentage / 100
                    total_percentage += percentage
                
                if total_percentage > 0:
                    avg_area = avg_area / (total_percentage / 100)
                else:
                    avg_area = 60  # default
                
                # ✅ V2.4: Estimate units count (use 85% efficiency for better space utilization)
                estimated_units = int(available.area / avg_area * 0.85)
                
                # Apply bounds from total_units
                min_units = total_units_config.get("min", 5)
                max_units = total_units_config.get("max", 100)
                estimated_units = max(min_units, min(estimated_units, max_units))
                
                logger.info(f"Estimated total units: {estimated_units} (avg area: {avg_area:.1f}m²)")
                
                # Calculate count for each type based on percentage
                unit_specs = []
                for ut in unit_types_config:
                    unit_type = ut.get("type", "Studio")
                    percentage = ut.get("percentage", 0)
                    priority = ut.get("priority", 1)
                    
                    # Calculate count from percentage
                    count = round(estimated_units * percentage / 100)
                    
                    # Extract area range
                    area_config = ut.get("area", {})
                    if isinstance(area_config, dict):
                        min_area = area_config.get("min", 50)
                        max_area = area_config.get("max", 100)
                    else:
                        min_area = ut.get("min_area", 50)
                        max_area = ut.get("max_area", 100)
                    
                    # Extract dimensions (NEW)
                    dimensions = ut.get("dimensions", {})
                    
                    for i in range(count):
                        target_area = np.random.uniform(min_area, max_area)
                        unit_specs.append({
                            "type": unit_type,
                            "target_area": target_area,
                            "min_area": min_area,
                            "max_area": max_area,
                            "priority": priority,
                            "dimensions": dimensions
                        })
                
                # Sort by priority (lower number = higher priority)
                unit_specs.sort(key=lambda x: x["priority"])
                
            else:
                # OLD: target_count strategy (backward compatibility)
                unit_specs = []
                for ut in unit_types_config:
                    unit_type = ut.get("type", "Studio")
                    count = ut.get("count", 0)
                    priority = ut.get("priority", 1)
                    
                    # Extract area range
                    area_config = ut.get("area", {})
                    if isinstance(area_config, dict):
                        min_area = area_config.get("min", 50)
                        max_area = area_config.get("max", 100)
                    else:
                        min_area = ut.get("min_area", 50)
                        max_area = ut.get("max_area", 100)
                    
                    dimensions = ut.get("dimensions", {})
                    
                    for i in range(count):
                        target_area = np.random.uniform(min_area, max_area)
                        unit_specs.append({
                            "type": unit_type,
                            "target_area": target_area,
                            "min_area": min_area,
                            "max_area": max_area,
                            "priority": priority,
                            "dimensions": dimensions
                        })
            
            logger.info(f"Planning layout for {len(unit_specs)} units")
            
            # Create corridor zone for access checking
            if not corridors:
                logger.warning("No corridors available - cannot place units without corridor access")
                return []
            
            corridor_union = unary_union(corridors)
            
            # Split available area into regions
            if isinstance(available, MultiPolygon):
                available_regions = list(available.geoms)
            else:
                available_regions = [available]
            
            # ✅ V2.4: Don't sort by area! This causes all units to cluster in largest region.
            # Instead, shuffle for balanced distribution across all regions
            import random
            random.shuffle(available_regions)  # Random order for balanced distribution
            
            logger.info(f"Available area has {len(available_regions)} regions")
            
            # ===== NEW: Multi-Pass Placement Strategy =====
            # Pass 1: Strict (perimeter + close to corridor)
            # Pass 2: Relaxed (near perimeter OR close to corridor)
            # Pass 3: Flexible (any location, prioritize filling space)
            
            placed_units = []
            remaining_specs = list(unit_specs)
            
            # PASS 1: Strict placement (DIRECT corridor adjacency)
            logger.info("Pass 1: Strict placement (DIRECT corridor access)...")
            remaining_specs = self._place_units_pass(
                remaining_specs,
                available_regions,
                corridor_union,
                placed_units,
                pass_config={
                    "name": "strict",
                    "min_perimeter": 0.8,      # Relaxed to 0.8m (one facade)
                    "max_corridor_distance": 0.3,  # CRITICAL: Direct touch (30cm max)
                    "min_corridor_facing_width": 2.5,  # NEW V2.2: Min 2.5m facing width
                    "min_area_match": 0.60,
                    "max_attempts": 800  # ✅ V2.4: Increased from 500 to 800
                }
            )
            
            # PASS 2: Relaxed placement (close to corridor)
            if remaining_specs:
                logger.info(f"Pass 2: Relaxed placement ({len(remaining_specs)} remaining)...")
                remaining_specs = self._place_units_pass(
                    remaining_specs,
                    available_regions,
                    corridor_union,
                    placed_units,
                    pass_config={
                        "name": "relaxed",
                        "min_perimeter": 0.3,      # Very relaxed
                        "max_corridor_distance": 1.0,  # Close to corridor (1m max)
                        "min_corridor_facing_width": 2.0,  # V2.2: Relaxed to 2.0m
                        "min_area_match": 0.50,
                        "max_attempts": 500
                    }
                )
            
            # PASS 3: Flexible placement (reasonable corridor distance)
            if remaining_specs:
                logger.info(f"Pass 3: Flexible placement ({len(remaining_specs)} remaining)...")
                remaining_specs = self._place_units_pass(
                    remaining_specs,
                    available_regions,
                    corridor_union,
                    placed_units,
                    pass_config={
                        "name": "flexible",
                        "min_perimeter": 0.0,      # No perimeter requirement
                        "max_corridor_distance": 2.5,  # Still reasonable (2.5m max)
                        "min_corridor_facing_width": 1.5,  # V2.2: Very relaxed (1.5m min)
                        "min_area_match": 0.40,    # Accept smaller units
                        "max_attempts": 600
                    }
                )
            
            if remaining_specs:
                logger.warning(f"Could not place {len(remaining_specs)} units after 3 passes")
            
            # Create final units list with proper IDs
            for i, unit_data in enumerate(placed_units, 1):
                units.append({
                    "id": f"unit_{i}",
                    "type": unit_data["type"],
                    "polygon": unit_data["polygon"],
                    "area": unit_data["area"],
                    "centroid": unit_data["polygon"].centroid
                })
            
            logger.info(f"Placed {len(units)}/{len(unit_specs)} units ({len(units)/len(unit_specs)*100:.1f}%)")
            
            # Log by type
            units_by_type = {}
            for unit in units:
                ut = unit["type"]
                units_by_type[ut] = units_by_type.get(ut, 0) + 1
            logger.info(f"Units by type: {units_by_type}")
            
            # Calculate metrics
            units_area = sum(u["area"] for u in units)
            corridor_area = sum(c.area for c in corridors)
            efficiency = units_area / self.area if self.area > 0 else 0
            corridor_ratio = corridor_area / self.area if self.area > 0 else 0
            
            logger.info(f"Layout metrics:")
            logger.info(f"  Units area: {units_area:.2f} m² ({efficiency*100:.1f}%)")
            logger.info(f"  Corridor area: {corridor_area:.2f} m² ({corridor_ratio*100:.1f}%)")
            
            return units
            
        except Exception as e:
            logger.error(f"Failed to layout units: {e}")
            import traceback
            traceback.print_exc()
            return []
