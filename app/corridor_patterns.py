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
    
    def _ensure_core_connection(self, corridors: List[Polygon]) -> List[Polygon]:
        """
        ✅ V2.4: Ensure ALL corridors connect to the core.
        Critical fix for isolated corridor problem.
        
        Args:
            corridors: List of corridor polygons
        
        Returns:
            Enhanced corridors list with core connections guaranteed
        """
        if not corridors:
            return corridors
        
        # Buffer core slightly for connection detection
        core_buffer = self.core.buffer(0.1)
        
        connected_corridors = []
        unconnected_corridors = []
        
        # Classify corridors
        for corridor in corridors:
            if corridor.intersects(core_buffer):
                connected_corridors.append(corridor)
            else:
                unconnected_corridors.append(corridor)
        
        # If NO corridors connect to core, extend the closest one
        if not connected_corridors and corridors:
            logger.warning("⚠️ NO corridors connect to core! Extending closest corridor...")
            
            # Find closest corridor to core
            closest_corridor = min(corridors, key=lambda c: c.distance(self.core))
            
            # Create connector from corridor to core
            core_point = self.core.centroid
            corridor_point = closest_corridor.centroid
            
            # Create connecting corridor
            connector = self._create_connecting_corridor(
                corridor_point,
                core_point,
                self.corridor_width
            )
            
            corridors.append(connector)
            logger.info("✅ Added connector to core")
        
        # Ensure main corridor network connects to core
        elif connected_corridors:
            corridor_network = unary_union(connected_corridors)
            
            # Connect unconnected corridors to network
            for uncorr in unconnected_corridors:
                if not uncorr.intersects(corridor_network.buffer(0.1)):
                    # Create connector
                    uncorr_point = uncorr.centroid
                    network_point = corridor_network.centroid
                    
                    connector = self._create_connecting_corridor(
                        uncorr_point,
                        network_point,
                        self.corridor_width
                    )
                    
                    corridors.append(connector)
                    logger.info("✅ Connected isolated corridor to network")
        
        return corridors
    
    def _create_connecting_corridor(self, point1, point2, width: float) -> Polygon:
        """
        Create a connecting corridor between two points.
        
        Args:
            point1: Start point
            point2: End point
            width: Corridor width
        
        Returns:
            Connecting corridor polygon
        """
        x1, y1 = point1.x, point1.y
        x2, y2 = point2.x, point2.y
        
        # Determine orientation (horizontal or vertical)
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        if dx > dy:
            # Horizontal connector
            connector = box(
                min(x1, x2),
                y1 - width / 2,
                max(x1, x2),
                y1 + width / 2
            )
        else:
            # Vertical connector
            connector = box(
                x1 - width / 2,
                min(y1, y2),
                x1 + width / 2,
                max(y1, y2)
            )
        
        # Clip to boundary
        if self.boundary.contains(connector):
            return connector
        else:
            return connector.intersection(self.boundary)
    
    def _create_grid_pattern(self, spacing: float = None) -> List[Polygon]:
        """
        ✅ V2.5.0: Create GRID pattern with parallel horizontal and vertical corridors.
        
        Best for: Large spaces (>2000 m²)
        Coverage: 95%+
        
        Grid pattern creates a network of intersecting corridors that covers
        the entire building, ensuring every unit is within walking distance.
        
        Args:
            spacing: Distance between parallel corridors (default: auto-calculated)
        
        Returns:
            List of corridor polygons forming a grid
        """
        if spacing is None:
            # Auto-calculate optimal spacing
            # Target: 10-12% corridor coverage (not 38%!)
            # Formula: fewer corridors, more space for units
            spacing = min(self.width, self.height) / 2.5  # Reduced from 3.5
            spacing = max(15.0, min(spacing, 30.0))  # Increased min from 10 to 15
        
        logger.info(f"Creating grid pattern with {spacing:.1f}m spacing")
        
        corridors = []
        
        # Horizontal corridors (2-3 main corridors, not 5-6)
        num_h_corridors = max(2, min(3, int(self.height / spacing)))
        for i in range(num_h_corridors):
            if num_h_corridors == 1:
                y = self.miny + self.height / 2
            else:
                y = self.miny + i * (self.height / (num_h_corridors - 1))
            
            corridor = box(
                self.minx,
                y - self.corridor_width / 2,
                self.maxx,
                y + self.corridor_width / 2
            )
            clipped = corridor.intersection(self.boundary)
            if not clipped.is_empty and clipped.area > 1.0:
                corridors.append(clipped)
        
        # Vertical corridors (2-3 main corridors, not 5-6)
        num_v_corridors = max(2, min(3, int(self.width / spacing)))
        for i in range(num_v_corridors):
            if num_v_corridors == 1:
                x = self.minx + self.width / 2
            else:
                x = self.minx + i * (self.width / (num_v_corridors - 1))
            
            corridor = box(
                x - self.corridor_width / 2,
                self.miny,
                x + self.corridor_width / 2,
                self.maxy
            )
            clipped = corridor.intersection(self.boundary)
            if not clipped.is_empty and clipped.area > 1.0:
                corridors.append(clipped)
        
        logger.info(f"Grid: {num_h_corridors} horizontal + {num_v_corridors} vertical = {len(corridors)} total")
        
        return corridors
    
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
        
        # ✅ V2.5.1: Optimized decision logic
        # For large spaces, use H pattern (better than grid)
        if self.area > 2500:
            return "H"  # H-pattern for large spaces (better coverage/corridor ratio)
        elif aspect_ratio > 2.5 or aspect_ratio < 0.4:
            return "L"  # Very elongated
        elif 0.85 <= aspect_ratio <= 1.15:
            if self.area > 2000:
                return "+"  # Medium-large square
            else:
                return "T"  # Medium square
        elif self.area > 1500:
            return "U"  # Large
        else:
            return "T"  # Small (default)
    
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
        if selected == "grid":  # ✅ V2.5.0: NEW Grid pattern
            corridors = self._create_grid_pattern()
        elif selected == "U":
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
        
        # ✅ V2.4: CRITICAL - Ensure core connection
        corridors = self._ensure_core_connection(corridors)
        
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
