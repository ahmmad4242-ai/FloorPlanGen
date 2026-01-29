"""
FloorPlanGen - Professional Corridor Network Builder
====================================================
Creates VISIBLE, LOGICAL corridor networks that SHOW in the floor plan!

Key principles:
- Wide corridors (min 2.5m for visibility)
- Clear main spine
- Visible branches to all units
- No thin/invisible corridors
"""

from shapely.geometry import Polygon, box, LineString, Point
from shapely.ops import unary_union
from typing import List, Dict, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


class VisibleCorridorBuilder:
    """
    Builds VISIBLE corridor networks that show clearly in floor plans.
    """
    
    def __init__(self, boundary: Polygon, core: Polygon):
        self.boundary = boundary
        self.core = core
        self.bounds = boundary.bounds
        self.minx, self.miny, self.maxx, self.maxy = self.bounds
        self.width = self.maxx - self.minx
        self.height = self.maxy - self.miny
        
        # Core bounds
        core_bounds = core.bounds
        self.core_minx, self.core_miny, self.core_maxx, self.core_maxy = core_bounds
        self.core_center_x = (self.core_minx + self.core_maxx) / 2
        self.core_center_y = (self.core_miny + self.core_maxy) / 2
    
    def build_double_loaded_network(self, corridor_width: float = 2.5) -> List[Polygon]:
        """
        Build VISIBLE double-loaded corridor network.
        
        Strategy:
        1. Main horizontal spine (full width) - ALWAYS VISIBLE
        2. Two vertical spines (left and right of core)
        3. Horizontal branches (north and south)
        
        This creates a CLEAR grid pattern that shows in the floor plan!
        """
        corridors = []
        
        # Ensure minimum width for visibility
        corridor_width = max(corridor_width, 2.5)
        
        logger.info(f"Building VISIBLE corridor network (width={corridor_width:.1f}m)")
        
        # 1. MAIN HORIZONTAL SPINE (full building width)
        # This is the PRIMARY circulation - must be VERY visible
        main_spine_y = self.core_center_y
        main_horizontal_spine = box(
            self.minx,
            main_spine_y - corridor_width / 2,
            self.maxx,
            main_spine_y + corridor_width / 2
        )
        corridors.append(main_horizontal_spine)
        logger.info(f"Main horizontal spine: {self.width:.1f}m long")
        
        # 2. VERTICAL SPINES (left and right of core)
        # These connect north-south circulation
        
        # Left vertical spine
        left_spine_x = self.core_minx - corridor_width * 1.5
        if left_spine_x > self.minx + corridor_width:
            left_vertical_spine = box(
                left_spine_x - corridor_width / 2,
                self.miny,
                left_spine_x + corridor_width / 2,
                self.maxy
            )
            corridors.append(left_vertical_spine)
            logger.info(f"Left vertical spine at x={left_spine_x:.1f}m")
        
        # Right vertical spine
        right_spine_x = self.core_maxx + corridor_width * 1.5
        if right_spine_x < self.maxx - corridor_width:
            right_vertical_spine = box(
                right_spine_x - corridor_width / 2,
                self.miny,
                right_spine_x + corridor_width / 2,
                self.maxy
            )
            corridors.append(right_vertical_spine)
            logger.info(f"Right vertical spine at x={right_spine_x:.1f}m")
        
        # 3. NORTH and SOUTH horizontal branches
        # These provide access to units away from main spine
        
        # North branch (above core)
        north_y = self.core_maxy + corridor_width * 2
        if north_y < self.maxy - corridor_width:
            north_branch = box(
                self.minx,
                north_y - corridor_width / 2,
                self.maxx,
                north_y + corridor_width / 2
            )
            corridors.append(north_branch)
            logger.info(f"North branch at y={north_y:.1f}m")
        
        # South branch (below core)
        south_y = self.core_miny - corridor_width * 2
        if south_y > self.miny + corridor_width:
            south_branch = box(
                self.minx,
                south_y - corridor_width / 2,
                self.maxx,
                south_y + corridor_width / 2
            )
            corridors.append(south_branch)
            logger.info(f"South branch at y={south_y:.1f}m")
        
        # 4. CORE CONNECTORS (ensure core is accessible)
        # Vertical connectors to core
        core_north_connector = box(
            self.core_center_x - corridor_width / 2,
            self.core_maxy,
            self.core_center_x + corridor_width / 2,
            main_spine_y + corridor_width / 2
        )
        corridors.append(core_north_connector)
        
        core_south_connector = box(
            self.core_center_x - corridor_width / 2,
            main_spine_y - corridor_width / 2,
            self.core_center_x + corridor_width / 2,
            self.core_miny
        )
        corridors.append(core_south_connector)
        
        # Clip all corridors to boundary
        clipped_corridors = []
        for corridor in corridors:
            clipped = corridor.intersection(self.boundary)
            if not clipped.is_empty and clipped.area > 0:
                clipped_corridors.append(clipped)
        
        # Merge overlapping corridors
        if clipped_corridors:
            corridor_union = unary_union(clipped_corridors)
            if hasattr(corridor_union, 'geoms'):
                final_corridors = list(corridor_union.geoms)
            else:
                final_corridors = [corridor_union]
        else:
            final_corridors = []
        
        total_corridor_area = sum(c.area for c in final_corridors)
        corridor_ratio = total_corridor_area / self.boundary.area
        
        logger.info(f"Corridor network complete:")
        logger.info(f"  Total area: {total_corridor_area:.1f} m²")
        logger.info(f"  Ratio: {corridor_ratio*100:.1f}% (target: 12-18%)")
        logger.info(f"  Segments: {len(final_corridors)}")
        
        return final_corridors
    
    def build_single_loaded_network(self, corridor_width: float = 2.5) -> List[Polygon]:
        """
        Build single-loaded corridor network (units on one side only).
        
        Strategy:
        1. Main corridor around core perimeter
        2. Branches to building perimeter
        """
        corridors = []
        
        # Ensure minimum width
        corridor_width = max(corridor_width, 2.5)
        
        # Ring corridor around core
        ring_offset = corridor_width * 1.5
        
        # Top
        top_corridor = box(
            self.core_minx - ring_offset,
            self.core_maxy,
            self.core_maxx + ring_offset,
            self.core_maxy + corridor_width
        )
        corridors.append(top_corridor)
        
        # Bottom
        bottom_corridor = box(
            self.core_minx - ring_offset,
            self.core_miny - corridor_width,
            self.core_maxx + ring_offset,
            self.core_miny
        )
        corridors.append(bottom_corridor)
        
        # Left
        left_corridor = box(
            self.core_minx - corridor_width,
            self.core_miny - ring_offset,
            self.core_minx,
            self.core_maxy + ring_offset
        )
        corridors.append(left_corridor)
        
        # Right
        right_corridor = box(
            self.core_maxx,
            self.core_miny - ring_offset,
            self.core_maxx + corridor_width,
            self.core_maxy + ring_offset
        )
        corridors.append(right_corridor)
        
        # Branches to perimeter
        # Left branch
        left_branch = box(
            self.minx,
            self.core_center_y - corridor_width / 2,
            self.core_minx - corridor_width,
            self.core_center_y + corridor_width / 2
        )
        corridors.append(left_branch)
        
        # Right branch
        right_branch = box(
            self.core_maxx + corridor_width,
            self.core_center_y - corridor_width / 2,
            self.maxx,
            self.core_center_y + corridor_width / 2
        )
        corridors.append(right_branch)
        
        # Clip and merge
        clipped_corridors = []
        for corridor in corridors:
            clipped = corridor.intersection(self.boundary)
            if not clipped.is_empty:
                clipped_corridors.append(clipped)
        
        if clipped_corridors:
            corridor_union = unary_union(clipped_corridors)
            if hasattr(corridor_union, 'geoms'):
                final_corridors = list(corridor_union.geoms)
            else:
                final_corridors = [corridor_union]
        else:
            final_corridors = []
        
        return final_corridors
