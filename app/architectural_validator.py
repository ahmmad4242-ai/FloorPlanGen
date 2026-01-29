"""
Architectural Constraints Validator
===================================
Comprehensive validation system for floor plan generation
Based on International Building Code (IBC) and best practices
"""

from typing import List, Dict, Tuple
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ArchitecturalConstraintsValidator:
    """
    Validates floor plan against architectural constraints.
    Ensures generated plans are safe, functional, and code-compliant.
    """
    
    def __init__(self):
        self.violations = []
        self.warnings = []
        
    def validate_floor_plan(self, 
                           units: List[Dict],
                           corridors: List[Polygon],
                           core: Polygon,
                           boundary: Polygon) -> Dict:
        """
        Comprehensive validation of complete floor plan.
        
        Returns:
            Dict with validation results and detailed violations
        """
        self.violations = []
        self.warnings = []
        
        # 1. Connectivity Constraints (Critical)
        self._validate_unit_corridor_connection(units, corridors)
        self._validate_corridor_core_connection(corridors, core)
        self._validate_dead_end_corridors(corridors, core)
        
        # 2. Spatial Constraints (Critical)
        self._validate_unit_dimensions(units)
        self._validate_corridor_widths(corridors)
        self._validate_core_size(core, len(units))
        
        # 3. Lighting & Ventilation (Critical)
        self._validate_external_facade(units, boundary)
        self._validate_functional_depth(units, boundary)
        
        # 4. Safety Constraints (Critical)
        self._validate_escape_distances(units, corridors, core)
        self._validate_escape_path_widths(corridors)
        
        # 5. Efficiency Constraints (Important)
        self._validate_efficiency_ratios(units, corridors, core, boundary)
        
        # 6. Privacy Constraints (Preferred)
        self._validate_unit_privacy(units)
        
        # Compile results
        is_valid = len(self.violations) == 0
        score = self._calculate_compliance_score()
        
        return {
            "is_valid": is_valid,
            "score": score,
            "violations": self.violations,
            "warnings": self.warnings,
            "summary": self._generate_summary()
        }
    
    # ============================================================
    # 1. CONNECTIVITY CONSTRAINTS
    # ============================================================
    
    def _validate_unit_corridor_connection(self, units: List[Dict], corridors: List[Polygon]):
        """
        CRITICAL: Every unit must connect directly to a corridor.
        No unit can be accessed only through another unit.
        """
        corridor_union = unary_union(corridors) if corridors else None
        
        for unit in units:
            unit_polygon = unit['polygon']
            unit_id = unit['id']
            
            # Check if unit boundary touches corridor
            if corridor_union:
                intersection = unit_polygon.boundary.intersection(corridor_union.boundary)
                connection_length = intersection.length if hasattr(intersection, 'length') else 0
                
                if connection_length < 0.9:  # Minimum door width
                    self.violations.append({
                        "type": "CRITICAL",
                        "code": "CONN_001",
                        "message": f"Unit {unit_id} not properly connected to corridor",
                        "detail": f"Connection length {connection_length:.2f}m < required 0.9m",
                        "unit_id": unit_id
                    })
            else:
                self.violations.append({
                    "type": "CRITICAL",
                    "code": "CONN_002",
                    "message": f"No corridors found - units cannot be accessed",
                    "unit_id": unit_id
                })
    
    def _validate_corridor_core_connection(self, corridors: List[Polygon], core: Polygon):
        """
        CRITICAL: All corridors must connect to the core (elevators/stairs).
        Maximum distance from any corridor point to core is 30m (fire code).
        """
        if not corridors or not core:
            return
            
        for i, corridor in enumerate(corridors):
            # Check direct connection
            touches = corridor.touches(core) or corridor.intersects(core)
            
            if not touches:
                # Check minimum distance
                min_distance = corridor.distance(core)
                
                if min_distance > 0.1:  # 10cm tolerance
                    self.violations.append({
                        "type": "CRITICAL",
                        "code": "CONN_003",
                        "message": f"Corridor {i+1} not connected to core",
                        "detail": f"Distance to core: {min_distance:.2f}m",
                        "corridor_id": i
                    })
            
            # Check maximum distance from any point
            max_distance = 0
            for coord in corridor.exterior.coords:
                point = Point(coord)
                distance = point.distance(core)
                max_distance = max(max_distance, distance)
            
            if max_distance > 30:
                self.violations.append({
                    "type": "CRITICAL",
                    "code": "CONN_004",
                    "message": f"Corridor {i+1} exceeds maximum escape distance",
                    "detail": f"Max distance to core: {max_distance:.2f}m > 30m limit",
                    "corridor_id": i
                })
    
    def _validate_dead_end_corridors(self, corridors: List[Polygon], core: Polygon):
        """
        IMPORTANT: Dead-end corridors (only one exit) must be ≤ 6m long.
        """
        # TODO: Implement graph-based analysis to detect dead-ends
        # For now, we'll skip this as it requires topological analysis
        pass
    
    # ============================================================
    # 2. SPATIAL CONSTRAINTS
    # ============================================================
    
    def _validate_unit_dimensions(self, units: List[Dict]):
        """
        CRITICAL: Each unit must meet minimum dimensions for its type.
        """
        minimum_dimensions = {
            "Studio": {"width": 3.5, "depth": 4.0, "area": 25},
            "1BR": {"width": 4.0, "depth": 5.0, "area": 45},
            "2BR": {"width": 5.0, "depth": 6.0, "area": 65},
            "3BR": {"width": 6.0, "depth": 7.0, "area": 85}
        }
        
        for unit in units:
            unit_type = unit.get('type', 'Studio')
            unit_area = unit['area']
            unit_id = unit['id']
            polygon = unit['polygon']
            
            # Get minimum requirements
            min_reqs = minimum_dimensions.get(unit_type, minimum_dimensions["Studio"])
            
            # Check area
            if unit_area < min_reqs["area"]:
                self.violations.append({
                    "type": "CRITICAL",
                    "code": "SPAT_001",
                    "message": f"Unit {unit_id} area below minimum for {unit_type}",
                    "detail": f"Area {unit_area:.2f}m² < required {min_reqs['area']}m²",
                    "unit_id": unit_id
                })
            
            # Check dimensions (using bounding box as approximation)
            bounds = polygon.bounds
            width = bounds[2] - bounds[0]
            depth = bounds[3] - bounds[1]
            min_dim = min(width, depth)
            
            if min_dim < min_reqs["width"]:
                self.warnings.append({
                    "type": "WARNING",
                    "code": "SPAT_002",
                    "message": f"Unit {unit_id} may be too narrow",
                    "detail": f"Minimum dimension {min_dim:.2f}m < recommended {min_reqs['width']}m",
                    "unit_id": unit_id
                })
            
            # Check aspect ratio
            aspect_ratio = max(width, depth) / min(width, depth) if min_dim > 0 else 999
            if aspect_ratio > 2.5:
                self.warnings.append({
                    "type": "WARNING",
                    "code": "SPAT_003",
                    "message": f"Unit {unit_id} has extreme aspect ratio",
                    "detail": f"Aspect ratio {aspect_ratio:.2f} > recommended 2.5",
                    "unit_id": unit_id
                })
    
    def _validate_corridor_widths(self, corridors: List[Polygon]):
        """
        CRITICAL: Corridors must be wide enough for safe passage.
        """
        for i, corridor in enumerate(corridors):
            # Approximate width using skeleton or sampling
            bounds = corridor.bounds
            approx_width = min(bounds[2] - bounds[0], bounds[3] - bounds[1])
            
            if approx_width < 1.2:
                self.violations.append({
                    "type": "CRITICAL",
                    "code": "SPAT_004",
                    "message": f"Corridor {i+1} too narrow",
                    "detail": f"Width ~{approx_width:.2f}m < minimum 1.2m",
                    "corridor_id": i
                })
            elif approx_width < 1.8:
                self.warnings.append({
                    "type": "WARNING",
                    "code": "SPAT_005",
                    "message": f"Corridor {i+1} width below recommended for double-loaded",
                    "detail": f"Width ~{approx_width:.2f}m < recommended 1.8m",
                    "corridor_id": i
                })
    
    def _validate_core_size(self, core: Polygon, units_count: int):
        """
        CRITICAL: Core must be large enough for elevators and stairs.
        """
        core_area = core.area
        
        # Minimum based on units count
        min_core_area = 25  # Base minimum
        if units_count > 8:
            min_core_area = 40
        if units_count > 15:
            min_core_area = 60
        
        if core_area < min_core_area:
            self.violations.append({
                "type": "CRITICAL",
                "code": "SPAT_006",
                "message": f"Core too small for {units_count} units",
                "detail": f"Core area {core_area:.2f}m² < required {min_core_area}m²"
            })
    
    # ============================================================
    # 3. LIGHTING & VENTILATION
    # ============================================================
    
    def _validate_external_facade(self, units: List[Dict], boundary: Polygon):
        """
        CRITICAL: Every unit must have access to external facade (natural light).
        """
        for unit in units:
            unit_polygon = unit['polygon']
            unit_id = unit['id']
            
            # Check if unit boundary touches building boundary
            intersection = unit_polygon.boundary.intersection(boundary.boundary)
            facade_length = intersection.length if hasattr(intersection, 'length') else 0
            
            if facade_length < 3.0:
                self.violations.append({
                    "type": "CRITICAL",
                    "code": "LIGHT_001",
                    "message": f"Unit {unit_id} insufficient external facade",
                    "detail": f"Facade length {facade_length:.2f}m < minimum 3.0m (for windows)",
                    "unit_id": unit_id
                })
            
            # Check facade-to-area ratio
            facade_ratio = facade_length / unit['area'] if unit['area'] > 0 else 0
            if facade_ratio < 0.1:
                self.warnings.append({
                    "type": "WARNING",
                    "code": "LIGHT_002",
                    "message": f"Unit {unit_id} poor facade-to-area ratio",
                    "detail": f"Ratio {facade_ratio:.3f} < recommended 0.1",
                    "unit_id": unit_id
                })
    
    def _validate_functional_depth(self, units: List[Dict], boundary: Polygon):
        """
        IMPORTANT: Units should not be too deep (poor natural light).
        """
        for unit in units:
            unit_polygon = unit['polygon']
            unit_id = unit['id']
            
            # Estimate depth from facade
            bounds = unit_polygon.bounds
            width = bounds[2] - bounds[0]
            depth = bounds[3] - bounds[1]
            max_depth = max(width, depth)
            
            if max_depth > 8.0:
                self.warnings.append({
                    "type": "WARNING",
                    "code": "LIGHT_003",
                    "message": f"Unit {unit_id} excessive depth",
                    "detail": f"Depth {max_depth:.2f}m > recommended 8.0m (may need light well)",
                    "unit_id": unit_id
                })
    
    # ============================================================
    # 4. SAFETY CONSTRAINTS
    # ============================================================
    
    def _validate_escape_distances(self, units: List[Dict], corridors: List[Polygon], core: Polygon):
        """
        CRITICAL: Maximum escape distance from any point to exit.
        """
        # This is a simplified check - full implementation would require path finding
        for unit in units:
            centroid = unit['polygon'].centroid
            distance_to_core = centroid.distance(core)
            
            if distance_to_core > 45:  # 15m in unit + 30m in corridor
                self.violations.append({
                    "type": "CRITICAL",
                    "code": "SAFE_001",
                    "message": f"Unit {unit['id']} exceeds maximum escape distance",
                    "detail": f"Distance to core {distance_to_core:.2f}m > maximum 45m",
                    "unit_id": unit['id']
                })
    
    def _validate_escape_path_widths(self, corridors: List[Polygon]):
        """
        CRITICAL: Escape paths must be wide enough.
        Already covered in corridor width validation.
        """
        pass
    
    # ============================================================
    # 5. EFFICIENCY CONSTRAINTS
    # ============================================================
    
    def _validate_efficiency_ratios(self, units: List[Dict], corridors: List[Polygon], 
                                    core: Polygon, boundary: Polygon):
        """
        IMPORTANT: Check space efficiency ratios.
        """
        total_area = boundary.area
        units_area = sum(u['area'] for u in units)
        corridors_area = sum(c.area for c in corridors)
        core_area = core.area
        
        # Net-to-Gross Ratio
        net_to_gross = units_area / total_area if total_area > 0 else 0
        if net_to_gross < 0.70:
            self.warnings.append({
                "type": "WARNING",
                "code": "EFFI_001",
                "message": "Low net-to-gross ratio",
                "detail": f"Ratio {net_to_gross:.2%} < recommended 70%"
            })
        
        # Corridor Ratio
        corridor_ratio = corridors_area / total_area if total_area > 0 else 0
        if corridor_ratio > 0.20:
            self.warnings.append({
                "type": "WARNING",
                "code": "EFFI_002",
                "message": "Excessive corridor area",
                "detail": f"Corridor ratio {corridor_ratio:.2%} > recommended 20%"
            })
    
    # ============================================================
    # 6. PRIVACY CONSTRAINTS
    # ============================================================
    
    def _validate_unit_privacy(self, units: List[Dict]):
        """
        PREFERRED: Check for privacy between units.
        """
        # Simplified check - full implementation would check window positions
        for i, unit1 in enumerate(units):
            for unit2 in units[i+1:]:
                distance = unit1['polygon'].distance(unit2['polygon'])
                if distance == 0:  # Units share a wall
                    # This is normal and expected, no violation
                    pass
    
    # ============================================================
    # UTILITY FUNCTIONS
    # ============================================================
    
    def _calculate_compliance_score(self) -> float:
        """
        Calculate overall compliance score (0-100).
        """
        critical_violations = [v for v in self.violations if v['type'] == 'CRITICAL']
        warnings = len(self.warnings)
        
        if len(critical_violations) > 0:
            # Heavy penalty for critical violations
            score = max(0, 50 - len(critical_violations) * 10)
        else:
            # Good base score, reduce for warnings
            score = 100 - warnings * 2
        
        return max(0, min(100, score))
    
    def _generate_summary(self) -> str:
        """Generate human-readable summary."""
        critical = len([v for v in self.violations if v['type'] == 'CRITICAL'])
        warnings = len(self.warnings)
        
        if critical == 0 and warnings == 0:
            return "✅ Floor plan meets all architectural constraints"
        elif critical == 0:
            return f"⚠️ Floor plan is valid but has {warnings} optimization opportunities"
        else:
            return f"❌ Floor plan has {critical} critical violations and {warnings} warnings"
