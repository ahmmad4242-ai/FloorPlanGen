"""
Advanced Corridor Pattern Generator V2.2

Supports multiple corridor patterns:
- U-pattern: 3-sided corridor
- L-pattern: 2 perpendicular corridors
- H-pattern: Double-loaded with cross
- Plus-pattern: 4-directional from center
- Line-pattern: Single straight corridor
- T-pattern: Current default (main spine + branch)
"""

from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class CorridorPatternGenerator:
    """Generate different corridor patterns for floor plans."""
    
    def __init__(self, boundary: Polygon, core: Polygon, corridor_width: float = 2.2):
        """
        Initialize corridor pattern generator.
        
        Args:
            boundary: Building boundary polygon
            core: Core (elevators, stairs) polygon
            corridor_width: Corridor width in meters
        """
        self.boundary = boundary
        self.core = core
        self.corridor_width = max(min(corridor_width, 2.5), 2.2)  # Clamp 2.2-2.5m
        
        # Get dimensions
        bounds = boundary.bounds
        self.minx, self.miny, self.maxx, self.maxy = bounds
        self.width = self.maxx - self.minx
        self.height = self.maxy - self.miny
        self.area = boundary.area
        
        # Core center
        self.core_center = core.centroid
        
        logger.info(f"Corridor generator initialized: {self.width:.1f}m × {self.height:.1f}m")
    
    def select_pattern(self, pattern: str = "auto") -> str:
        """
        Auto-select best corridor pattern based on building shape.
        
        Args:
            pattern: "auto" or specific pattern name
        
        Returns:
            Selected pattern name
        """
        if pattern != "auto":
            return pattern
        
        aspect_ratio = self.width / self.height if self.height > 0 else 1.0
        
        logger.info(f"Auto-selecting pattern: aspect={aspect_ratio:.2f}, area={self.area:.0f}m²")
        
        # Decision logic
        if aspect_ratio > 2.5 or aspect_ratio < 0.4:
            return "L"  # Very elongated
        elif 0.85 <= aspect_ratio <= 1.15:
            if self.area > 3000:
                return "H"  # Large square
            else:
                return "+"  # Medium square
        elif self.area > 5000:
            return "H"  # Very large
        elif self.area > 2500:
            return "U"  # Large
        else:
            return "T"  # Medium (default)
    
    def generate(self, pattern: str = "auto", usable_area: Polygon = None) -> List[Polygon]:
        """
        Generate corridor network with specified pattern.
        
        Args:
            pattern: Pattern type or "auto"
            usable_area: Usable area polygon (for intersection)
        
        Returns:
            List of corridor polygons
        """
        selected = self.select_pattern(pattern)
        logger.info(f"Generating {selected}-pattern corridors")
        
        # Generate pattern
        if selected == "U":
            corridors = self._create_U_pattern()
        elif selected == "L":
            corridors = self._create_L_pattern()
        elif selected == "H":
            corridors = self._create_H_pattern()
        elif selected == "+":
            corridors = self._create_plus_pattern()
        elif selected == "line":
            corridors = self._create_line_pattern()
        else:  # T-pattern (default)
            corridors = self._create_T_pattern()
        
        # Intersect with usable area if provided
        if usable_area:
            clipped = []
            for corridor in corridors:
                clipped_corridor = corridor.intersection(usable_area)
                if not clipped_corridor.is_empty:
                    clipped.append(clipped_corridor)
            corridors = clipped
        
        # Log results
        total_area = sum(c.area for c in corridors)
        ratio = total_area / self.area * 100 if self.area > 0 else 0
        logger.info(f"Created {len(corridors)} corridors: {total_area:.1f}m² ({ratio:.1f}%)")
        
        return corridors
    
    def _create_U_pattern(self) -> List[Polygon]:
        """
        U-shaped corridor: 3 sides (left, bottom, right).
        Core typically at top center.
        """
        w = self.corridor_width
        corridors = []
        
        # Left vertical corridor (80% of height)
        left_height = self.height * 0.8
        left = box(
            self.minx + w,
            self.miny + self.height * 0.1,
            self.minx + w * 2,
            self.miny + self.height * 0.1 + left_height
        )
        corridors.append(left)
        
        # Bottom horizontal corridor (full width)
        bottom = box(
            self.minx + w,
            self.miny + w,
            self.maxx - w,
            self.miny + w * 2
        )
        corridors.append(bottom)
        
        # Right vertical corridor (80% of height)
        right = box(
            self.maxx - w * 2,
            self.miny + self.height * 0.1,
            self.maxx - w,
            self.miny + self.height * 0.1 + left_height
        )
        corridors.append(right)
        
        logger.info("Created U-pattern: 3 corridors (left, bottom, right)")
        return corridors
    
    def _create_L_pattern(self) -> List[Polygon]:
        """
        L-shaped corridor: 2 perpendicular corridors.
        Core at junction.
        """
        w = self.corridor_width
        corridors = []
        
        # Horizontal corridor (left to center)
        horiz = box(
            self.minx,
            self.core_center.y - w / 2,
            self.core_center.x + w,
            self.core_center.y + w / 2
        )
        corridors.append(horiz)
        
        # Vertical corridor (bottom to center)
        vert = box(
            self.core_center.x - w / 2,
            self.miny,
            self.core_center.x + w / 2,
            self.core_center.y + w
        )
        corridors.append(vert)
        
        logger.info("Created L-pattern: 2 perpendicular corridors")
        return corridors
    
    def _create_H_pattern(self) -> List[Polygon]:
        """
        H-shaped corridor: 2 parallel corridors + cross connector.
        Double-loaded with center connection.
        """
        w = self.corridor_width
        corridors = []
        
        # Left vertical corridor
        left_x = self.minx + self.width * 0.25
        left = box(
            left_x - w / 2,
            self.miny + w,
            left_x + w / 2,
            self.maxy - w
        )
        corridors.append(left)
        
        # Right vertical corridor
        right_x = self.maxx - self.width * 0.25
        right = box(
            right_x - w / 2,
            self.miny + w,
            right_x + w / 2,
            self.maxy - w
        )
        corridors.append(right)
        
        # Center horizontal connector
        center = box(
            left_x + w / 2,
            self.core_center.y - w / 2,
            right_x - w / 2,
            self.core_center.y + w / 2
        )
        corridors.append(center)
        
        logger.info("Created H-pattern: 2 parallel + 1 cross corridors")
        return corridors
    
    def _create_plus_pattern(self) -> List[Polygon]:
        """
        Plus/Cross pattern: 4 directions from center (N, S, E, W).
        Core at center.
        """
        w = self.corridor_width
        corridors = []
        
        # North corridor
        north = box(
            self.core_center.x - w / 2,
            self.core_center.y + w / 2,
            self.core_center.x + w / 2,
            self.maxy - w
        )
        corridors.append(north)
        
        # South corridor
        south = box(
            self.core_center.x - w / 2,
            self.miny + w,
            self.core_center.x + w / 2,
            self.core_center.y - w / 2
        )
        corridors.append(south)
        
        # East corridor
        east = box(
            self.core_center.x + w / 2,
            self.core_center.y - w / 2,
            self.maxx - w,
            self.core_center.y + w / 2
        )
        corridors.append(east)
        
        # West corridor
        west = box(
            self.minx + w,
            self.core_center.y - w / 2,
            self.core_center.x - w / 2,
            self.core_center.y + w / 2
        )
        corridors.append(west)
        
        logger.info("Created Plus-pattern: 4 directional corridors")
        return corridors
    
    def _create_line_pattern(self) -> List[Polygon]:
        """
        Single straight corridor (single-loaded or double-loaded).
        Orientation based on building aspect ratio.
        """
        w = self.corridor_width
        corridors = []
        
        if self.width >= self.height:
            # Horizontal corridor
            corridor = box(
                self.minx,
                self.core_center.y - w / 2,
                self.maxx,
                self.core_center.y + w / 2
            )
        else:
            # Vertical corridor
            corridor = box(
                self.core_center.x - w / 2,
                self.miny,
                self.core_center.x + w / 2,
                self.maxy
            )
        
        corridors.append(corridor)
        logger.info("Created Line-pattern: 1 straight corridor")
        return corridors
    
    def _create_T_pattern(self) -> List[Polygon]:
        """
        T-shaped corridor: Main spine + perpendicular branch.
        Current default pattern.
        """
        w = self.corridor_width
        corridors = []
        
        if self.width >= self.height:
            # Horizontal main + vertical branch
            # Main horizontal spine
            main = box(
                self.minx,
                self.core_center.y - w / 2,
                self.maxx,
                self.core_center.y + w / 2
            )
            corridors.append(main)
            
            # Vertical branch (80% extension)
            branch_length = self.height * 0.8 / 2
            branch = box(
                self.core_center.x - w / 2,
                self.core_center.y - branch_length,
                self.core_center.x + w / 2,
                self.core_center.y + branch_length
            )
            corridors.append(branch)
        else:
            # Vertical main + horizontal branch
            # Main vertical spine
            main = box(
                self.core_center.x - w / 2,
                self.miny,
                self.core_center.x + w / 2,
                self.maxy
            )
            corridors.append(main)
            
            # Horizontal branch (80% extension)
            branch_length = self.width * 0.8 / 2
            branch = box(
                self.core_center.x - branch_length,
                self.core_center.y - w / 2,
                self.core_center.x + branch_length,
                self.core_center.y + w / 2
            )
            corridors.append(branch)
        
        logger.info("Created T-pattern: Main spine + branch")
        return corridors
