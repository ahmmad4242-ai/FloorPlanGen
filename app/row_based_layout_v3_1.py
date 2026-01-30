"""
FloorPlanGen V3.1 - Simplified Row-Based Layout
==============================================
Date: 2026-01-30
Goal: 95%+ coverage with simple row-based placement

Key Changes from V3.0:
1. Simpler row creation - divide available area into horizontal strips
2. Each row covers FULL width of available area
3. Place units side-by-side in each row
4. No complex corridor orientation detection

Algorithm:
1. Get available_area (boundary - core - corridors)
2. Divide into N horizontal rows (row_height = 8m default)
3. Fill each row with units from left to right
4. Ensure units have corridor access via proximity check
"""

from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class RowBasedLayoutV31:
    """V3.1 - Simplified Row-Based Layout for 95%+ coverage"""
    
    def __init__(self, boundary: Polygon, corridors: List[Polygon], core: Polygon):
        self.boundary = boundary
        self.corridors = corridors
        self.core = core
        self.corridor_union = unary_union(corridors) if corridors else Polygon()
        
        # Compute available area
        occupied = [core] if core and not core.is_empty else []
        if corridors:
            occupied.extend(corridors)
        occupied_union = unary_union(occupied) if occupied else Polygon()
        self.available_area = boundary.difference(occupied_union)
        
        logger.info(f"V3.1 Initialized - Available area: {self.available_area.area:.2f} m²")
    
    def create_simple_rows(self, row_height: float = 8.0) -> List[Dict]:
        """
        Divide available area into simple horizontal rows
        
        Args:
            row_height: Height of each row in meters (default 8m)
            
        Returns:
            List of row dictionaries with polygon, y_min, y_max
        """
        if self.available_area.is_empty:
            logger.warning("No available area to create rows")
            return []
        
        rows = []
        minx, miny, maxx, maxy = self.available_area.bounds
        
        # Create horizontal strips from bottom to top
        current_y = miny
        row_id = 1
        
        while current_y < maxy:
            next_y = min(current_y + row_height, maxy)
            
            # Create row box
            row_box = box(minx, current_y, maxx, next_y)
            
            # Intersect with available area
            row_poly = row_box.intersection(self.available_area)
            
            if not row_poly.is_empty and row_poly.area > 10.0:  # Min 10 m² row
                rows.append({
                    'id': row_id,
                    'polygon': row_poly,
                    'y_min': current_y,
                    'y_max': next_y,
                    'height': next_y - current_y
                })
                logger.debug(f"Row {row_id}: Area {row_poly.area:.2f} m², Y: {current_y:.1f}-{next_y:.1f}")
                row_id += 1
            
            current_y = next_y
        
        logger.info(f"Created {len(rows)} rows with total area {sum(r['polygon'].area for r in rows):.2f} m²")
        return rows
    
    def fill_row_with_units(self, row: Dict, unit_specs: List[Dict]) -> List[Dict]:
        """
        Fill a single row with units from left to right
        
        Args:
            row: Row dictionary with polygon, y_min, y_max
            unit_specs: List of unit specifications sorted by target_area (large to small)
            
        Returns:
            List of placed unit dictionaries
        """
        placed_units = []
        row_poly = row['polygon']
        row_height = row['height']
        
        minx, miny, maxx, maxy = row_poly.bounds
        current_x = minx
        
        for spec in unit_specs:
            if current_x >= maxx - 0.5:  # No space left in row
                break
            
            target_area = spec['target_area']
            unit_width = target_area / row_height  # Width = Area / Height
            
            # Create unit box
            unit_box = box(current_x, miny, min(current_x + unit_width, maxx), maxy)
            
            # Clip to row polygon
            unit_clipped = unit_box.intersection(row_poly)
            
            if unit_clipped.is_empty or not isinstance(unit_clipped, Polygon):
                current_x += unit_width * 0.5  # Try shifting
                continue
            
            # Check minimum area (at least 60% of target)
            if unit_clipped.area < target_area * 0.6:
                current_x += unit_width * 0.5
                continue
            
            # Check corridor proximity (unit should be near corridor)
            if not self.corridor_union.is_empty:
                distance = unit_clipped.distance(self.corridor_union)
                if distance > 15.0:  # Too far from corridor
                    logger.debug(f"Unit too far from corridor: {distance:.2f}m")
                    current_x += unit_width * 0.5
                    continue
            
            # Place unit
            placed_units.append({
                'type': spec['unit_type'],
                'polygon': unit_clipped,
                'area': unit_clipped.area,
                'centroid': (unit_clipped.centroid.x, unit_clipped.centroid.y),
                'target_area': target_area
            })
            
            logger.debug(f"Placed {spec['unit_type']}: {unit_clipped.area:.2f} m² at x={current_x:.1f}")
            current_x += unit_width  # Move to next position
        
        return placed_units
    
    def layout_units_row_based(self, unit_constraints: Dict) -> List[Dict]:
        """
        Main entry point - layout units using row-based approach
        
        Args:
            unit_constraints: Unit specifications and constraints
            
        Returns:
            List of placed unit dictionaries
        """
        logger.info("=" * 60)
        logger.info("V3.1 ROW-BASED LAYOUT - Starting")
        logger.info("=" * 60)
        
        # Get unit specs
        units_config = unit_constraints.get('units', [])
        generation_strategy = unit_constraints.get('generation_strategy', 'fill_available')
        
        if not units_config:
            logger.warning("No unit configurations provided")
            return []
        
        # Estimate total units needed
        available_area = self.available_area.area
        avg_unit_area = sum(u.get('area', {}).get('target', 50) for u in units_config) / len(units_config)
        estimated_units = int(available_area / avg_unit_area * 0.85)  # 85% fill target
        
        logger.info(f"Available area: {available_area:.2f} m²")
        logger.info(f"Estimated units: {estimated_units}")
        logger.info(f"Average unit area: {avg_unit_area:.2f} m²")
        
        # Create unit specs list
        unit_specs = []
        for unit_config in units_config:
            unit_type = unit_config['type']
            target_area = unit_config.get('area', {}).get('target', 50)
            percentage = unit_config.get('percentage', 0) / 100.0
            count = int(estimated_units * percentage)
            
            for i in range(count):
                unit_specs.append({
                    'unit_type': unit_type,
                    'target_area': target_area
                })
        
        # Sort by area (large to small)
        unit_specs.sort(key=lambda x: x['target_area'], reverse=True)
        logger.info(f"Generated {len(unit_specs)} unit specs")
        
        # Create rows
        row_height = 8.0  # Standard row height
        rows = self.create_simple_rows(row_height)
        
        if not rows:
            logger.warning("No rows created - returning empty list")
            return []
        
        # Fill rows with units
        all_placed_units = []
        remaining_specs = unit_specs.copy()
        
        for row in rows:
            if not remaining_specs:
                break
            
            # Calculate how many units can fit in this row
            row_area = row['polygon'].area
            specs_for_row = []
            current_area = 0
            
            for spec in remaining_specs[:]:
                if current_area + spec['target_area'] <= row_area * 1.2:  # Allow 20% overfill
                    specs_for_row.append(spec)
                    current_area += spec['target_area']
                    remaining_specs.remove(spec)
            
            if specs_for_row:
                placed = self.fill_row_with_units(row, specs_for_row)
                all_placed_units.extend(placed)
                logger.info(f"Row {row['id']}: Placed {len(placed)} units ({sum(u['area'] for u in placed):.2f} m²)")
        
        logger.info("=" * 60)
        logger.info(f"V3.1 COMPLETE - Placed {len(all_placed_units)} units")
        logger.info(f"Total area: {sum(u['area'] for u in all_placed_units):.2f} m²")
        logger.info(f"Remaining specs: {len(remaining_specs)}")
        logger.info("=" * 60)
        
        return all_placed_units


def layout_units_v31(boundary: Polygon, corridors: List[Polygon], core: Polygon, 
                     unit_constraints: Dict) -> List[Dict]:
    """
    Convenience function for V3.1 row-based layout
    
    Args:
        boundary: Building boundary polygon
        corridors: List of corridor polygons
        core: Core polygon
        unit_constraints: Unit specifications
        
    Returns:
        List of placed unit dictionaries
    """
    engine = RowBasedLayoutV31(boundary, corridors, core)
    return engine.layout_units_row_based(unit_constraints)


logger.info("✅ V3.1 Simplified Row-Based Layout Module Loaded")
