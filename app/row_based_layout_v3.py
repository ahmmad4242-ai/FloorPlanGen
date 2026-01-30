"""
V3.0 - Row-Based Layout Algorithm
==================================
Revolutionary approach for 95%+ coverage:
- No region.difference() fragmentation!
- Units arranged in rows (like parking)
- Predictable, efficient space utilization

Author: FloorPlanGen V3.0
Date: 2026-01-30
"""

from shapely.geometry import Polygon, box, LineString, Point, MultiPolygon
from shapely.ops import unary_union
from typing import List, Dict, Tuple, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class RowBasedLayoutV3:
    """
    V3.0: Row-Based Layout Engine for 95%+ coverage.
    
    Key Innovation:
    - Place units in rows (side-by-side)
    - No region fragmentation
    - Corridor-aware placement
    """
    
    def __init__(self, boundary: Polygon, corridors: List[Polygon], core: Polygon):
        self.boundary = boundary
        self.corridors = corridors
        self.core = core
        self.corridor_union = unary_union(corridors) if corridors else Polygon()
        
        # Calculate available area
        occupied = unary_union([core] + corridors)
        self.available_area = boundary.difference(occupied)
        
        logger.info(f"✅ V3.0 Row-Based Layout initialized")
        logger.info(f"   Available area: {self.available_area.area:.1f} m²")
    
    def detect_corridor_orientation(self) -> str:
        """
        Detect primary corridor orientation.
        
        Returns:
            'horizontal', 'vertical', or 'mixed'
        """
        if not self.corridors:
            return 'horizontal'
        
        horizontal_length = 0
        vertical_length = 0
        
        for corridor in self.corridors:
            minx, miny, maxx, maxy = corridor.bounds
            width = maxx - minx
            height = maxy - miny
            
            if width > height * 1.5:
                horizontal_length += width
            elif height > width * 1.5:
                vertical_length += height
            else:
                horizontal_length += width * 0.5
                vertical_length += height * 0.5
        
        logger.info(f"   Corridor analysis: H={horizontal_length:.1f}m, V={vertical_length:.1f}m")
        
        if horizontal_length > vertical_length * 1.3:
            return 'horizontal'
        elif vertical_length > horizontal_length * 1.3:
            return 'vertical'
        else:
            return 'mixed'
    
    def split_into_rows(self, unit_depth_avg: float = 8.0) -> List[Dict]:
        """
        Split available_area into rows for unit placement.
        
        Args:
            unit_depth_avg: Average unit depth (perpendicular to row direction)
        
        Returns:
            List of row dictionaries with 'polygon', 'direction', 'corridor'
        """
        orientation = self.detect_corridor_orientation()
        
        if orientation == 'horizontal':
            return self._split_perpendicular_to_corridors('horizontal', unit_depth_avg)
        elif orientation == 'vertical':
            return self._split_perpendicular_to_corridors('vertical', unit_depth_avg)
        else:
            return self._split_simple_grid(unit_depth_avg)
    
    def _split_perpendicular_to_corridors(self, corridor_orientation: str, 
                                          unit_depth: float) -> List[Dict]:
        """
        ✅ V3.0.2: FIXED - Create rows that cover ALL available space, not just narrow strips!
        
        Split area perpendicular to corridor orientation.
        """
        rows = []
        
        # Get available_area bounds
        avail_minx, avail_miny, avail_maxx, avail_maxy = self.available_area.bounds
        
        if corridor_orientation == 'horizontal':
            # Corridors run horizontally (x-direction)
            # Create vertical rows along the entire Y-axis range
            
            # For each corridor, create rows on both sides covering the full available space
            for corridor in self.corridors:
                c_minx, c_miny, c_maxx, c_maxy = corridor.bounds
                
                # Row above corridor - extends from corridor top to boundary top
                row_above = box(
                    avail_minx,  # Use full available width
                    c_maxy,      # Start at corridor top
                    avail_maxx,  # Use full available width
                    avail_maxy   # Extend to boundary top
                )
                
                # Row below corridor - extends from boundary bottom to corridor bottom
                row_below = box(
                    avail_minx,  # Use full available width
                    avail_miny,  # Start at boundary bottom
                    avail_maxx,  # Use full available width
                    c_miny       # End at corridor bottom
                )
                
                # Clip to available_area and add
                for row_poly in [row_above, row_below]:
                    clipped = row_poly.intersection(self.available_area)
                    if not clipped.is_empty and clipped.area > 10:
                        rows.append({
                            'polygon': clipped,
                            'direction': 'horizontal',  # Units placed horizontally (along X)
                            'corridor': corridor
                        })
        
        else:  # vertical corridors
            # Corridors run vertically (y-direction)
            # Create horizontal rows along the entire X-axis range
            
            for corridor in self.corridors:
                c_minx, c_miny, c_maxx, c_maxy = corridor.bounds
                
                # Row to the right - extends from corridor right to boundary right
                row_right = box(
                    c_maxx,      # Start at corridor right
                    avail_miny,  # Use full available height
                    avail_maxx,  # Extend to boundary right
                    avail_maxy   # Use full available height
                )
                
                # Row to the left - extends from boundary left to corridor left
                row_left = box(
                    avail_minx,  # Start at boundary left
                    avail_miny,  # Use full available height
                    c_minx,      # End at corridor left
                    avail_maxy   # Use full available height
                )
                
                # Clip and add
                for row_poly in [row_right, row_left]:
                    clipped = row_poly.intersection(self.available_area)
                    if not clipped.is_empty and clipped.area > 10:
                        rows.append({
                            'polygon': clipped,
                            'direction': 'vertical',  # Units placed vertically (along Y)
                            'corridor': corridor
                        })
        
        logger.info(f"   ✅ V3.0.2: Created {len(rows)} FULL-SIZE rows perpendicular to {corridor_orientation} corridors")
        return rows
    
    def _split_simple_grid(self, unit_depth: float) -> List[Dict]:
        """
        Fallback: Simple grid-based row splitting.
        """
        rows = []
        minx, miny, maxx, maxy = self.available_area.bounds
        
        y = miny
        while y < maxy:
            row_poly = box(minx, y, maxx, min(y + unit_depth, maxy))
            clipped = row_poly.intersection(self.available_area)
            
            if not clipped.is_empty and clipped.area > 10:
                rows.append({
                    'polygon': clipped,
                    'direction': 'horizontal',
                    'corridor': self.corridor_union
                })
            
            y += unit_depth
        
        logger.info(f"   Created {len(rows)} rows using simple grid")
        return rows
    
    def fill_row_with_units(self, row: Dict, unit_specs: List[Dict]) -> List[Dict]:
        """
        Fill a single row with units, side-by-side.
        
        FIXED V3.0.1: Correct calculation of unit dimensions based on row geometry.
        """
        placed_units = []
        row_poly = row['polygon']
        direction = row['direction']
        
        minx, miny, maxx, maxy = row_poly.bounds
        
        if direction == 'horizontal':
            # Units placed left-to-right along x-axis
            current_pos = minx
            end_pos = maxx
            row_length = maxx - minx  # Length along which units are placed
            row_depth = maxy - miny    # Depth perpendicular to placement
        else:  # vertical
            # Units placed bottom-to-top along y-axis
            current_pos = miny
            end_pos = maxy
            row_length = maxy - miny   # Length along which units are placed
            row_depth = maxx - minx    # Depth perpendicular to placement
        
        logger.debug(f"   Row: length={row_length:.1f}m, depth={row_depth:.1f}m, direction={direction}")
        
        # ✅ CRITICAL FIX: Check if row_depth is valid
        if row_depth < 3.0:  # Minimum viable depth for a unit
            logger.warning(f"   Row too shallow ({row_depth:.1f}m), skipping")
            return []
        
        # Sort by size (largest first for better fitting)
        sorted_specs = sorted(unit_specs, key=lambda s: s['target_area'], reverse=True)
        
        placed_count = 0
        for spec in sorted_specs:
            target_area = spec['target_area']
            unit_type = spec['type']
            
            # ✅ CRITICAL FIX: Calculate unit width based on target_area and row_depth
            # Unit occupies full row_depth, calculate required width
            unit_width = target_area / row_depth
            
            # Check if unit fits in remaining row space
            if current_pos + unit_width <= end_pos + 0.1:  # 0.1m tolerance
                # Create unit polygon
                if direction == 'horizontal':
                    # Unit extends along x-axis
                    unit_poly = box(current_pos, miny, current_pos + unit_width, maxy)
                else:  # vertical
                    # Unit extends along y-axis
                    unit_poly = box(minx, current_pos, maxx, current_pos + unit_width)
                
                # Clip to row_poly (handle irregular shapes)
                unit_clipped = unit_poly.intersection(row_poly)
                
                if not unit_clipped.is_empty and isinstance(unit_clipped, Polygon):
                    # ✅ Accept if at least 60% of target (more lenient)
                    if unit_clipped.area >= target_area * 0.60:
                        placed_units.append({
                            'polygon': unit_clipped,
                            'type': unit_type,
                            'area': unit_clipped.area
                        })
                        current_pos += unit_width
                        placed_count += 1
                        logger.debug(f"      Placed {unit_type}: {unit_clipped.area:.1f} m²")
        
        logger.debug(f"   Placed {placed_count} units in this row")
        return placed_units
    
    def layout_units_row_based(self, unit_specs: List[Dict]) -> List[Dict]:
        """
        V3.0: Main entry point for row-based unit placement.
        """
        logger.info("🚀 V3.0 Row-Based Layout: Starting...")
        
        if not unit_specs:
            logger.warning("No unit specs provided")
            return []
        
        avg_area = sum(s['target_area'] for s in unit_specs) / len(unit_specs)
        unit_depth_avg = np.sqrt(avg_area * 1.3)
        
        logger.info(f"   Average unit depth: {unit_depth_avg:.1f}m")
        
        rows = self.split_into_rows(unit_depth_avg)
        
        if not rows:
            logger.error("   No rows created!")
            return []
        
        logger.info(f"   Created {len(rows)} rows")
        
        all_placed_units = []
        remaining_specs = list(unit_specs)
        
        for i, row in enumerate(rows):
            if not remaining_specs:
                break
            
            row_area = row['polygon'].area
            avg_unit_area = sum(s['target_area'] for s in remaining_specs) / len(remaining_specs)
            units_for_this_row = max(1, int(row_area / avg_unit_area * 0.9))
            
            row_specs = remaining_specs[:units_for_this_row]
            placed_in_row = self.fill_row_with_units(row, row_specs)
            
            all_placed_units.extend(placed_in_row)
            placed_count = len(placed_in_row)
            remaining_specs = remaining_specs[placed_count:]
        
        logger.info(f"✅ V3.0: Placed {len(all_placed_units)} units")
        return all_placed_units


logger.info("✅ V3.0 Row-Based Layout module loaded")
