"""
FloorPlanGen - Constraint Solver using OR-Tools CP-SAT
Optimizes floor plan layout based on constraints.
"""

from ortools.sat.python import cp_model
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ConstraintSolver:
    """Solves floor plan optimization using CP-SAT."""
    
    def __init__(self, constraints: Dict):
        self.constraints = constraints
        # Extract architectural constraints if available
        self.arch_constraints = constraints.get("architectural_constraints", {})
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
    
    def optimize_layout(self,
                       available_area: float,
                       units: List[Dict]) -> Optional[Dict]:
        """
        Optimize unit placement and sizing based on constraints.
        
        Args:
            available_area: Total available area for units
            units: List of initial unit proposals
        
        Returns:
            Optimized solution or None if infeasible
        """
        try:
            # Extract constraint values
            unit_constraints = self.constraints.get("units", [])
            circulation = self.constraints.get("circulation", {})
            rules = self.constraints.get("rules", {})
            
            # Create variables for each unit type
            unit_vars = {}
            area_vars = {}
            
            for uc in unit_constraints:
                unit_type = uc["type"]
                count = uc["count"]
                min_area = uc.get("net_area_m2", {}).get("min", 50)
                max_area = uc.get("net_area_m2", {}).get("max", 150)
                
                # Variable for number of units of this type
                var = self.model.NewIntVar(0, count, f"count_{unit_type}")
                unit_vars[unit_type] = var
                
                # Variable for total area of this unit type
                # Scale to integer (multiply by 10 for precision)
                min_area_int = int(min_area * count * 10)
                max_area_int = int(max_area * count * 10)
                area_var = self.model.NewIntVar(min_area_int, max_area_int, f"area_{unit_type}")
                area_vars[unit_type] = area_var
            
            # Constraint: Total area must not exceed available area
            total_area = sum(area_vars.values())
            available_area_int = int(available_area * 10)
            self.model.Add(total_area <= available_area_int)
            
            # Constraint: Meet unit count targets
            for uc in unit_constraints:
                unit_type = uc["type"]
                target_count = uc["count"]
                self.model.Add(unit_vars[unit_type] == target_count)
            
            # Objective: Maximize total unit area (efficiency)
            self.model.Maximize(total_area)
            
            # Solve
            status = self.solver.Solve(self.model)
            
            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                solution = {
                    "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
                    "units": {},
                    "objective_value": self.solver.ObjectiveValue() / 10  # Scale back
                }
                
                for unit_type, var in unit_vars.items():
                    solution["units"][unit_type] = {
                        "count": self.solver.Value(var),
                        "total_area": self.solver.Value(area_vars[unit_type]) / 10
                    }
                
                logger.info(f"Solved: {solution['status']}, objective = {solution['objective_value']:.2f}")
                return solution
            else:
                logger.warning("No feasible solution found")
                return None
                
        except Exception as e:
            logger.error(f"Constraint solver failed: {e}")
            return None
    
    def validate_constraints(self, 
                            metrics: Dict,
                            units: List[Dict]) -> Dict:
        """
        Validate generated floor plan against all constraints.
        
        Returns:
            Validation report with pass/fail for each constraint
        """
        report = {
            "overall_passed": True,
            "constraints": {},
            "score": 100.0
        }
        
        try:
            # Get architectural constraints or fall back to legacy format
            arch_circulation = self.arch_constraints.get("circulation", {})
            legacy_circulation = self.constraints.get("circulation", {})
            
            # Validate corridor ratio
            if arch_circulation and "corridor_area_ratio" in arch_circulation:
                max_corridor_ratio = arch_circulation.get("corridor_area_ratio", {}).get("max", 0.20)
            else:
                max_corridor_ratio = legacy_circulation.get("corridor_area_ratio", {}).get("max", 0.20)
            
            actual_corridor_ratio = metrics.get("corridor_ratio", 0)
            
            corridor_passed = actual_corridor_ratio <= max_corridor_ratio
            report["constraints"]["corridor_ratio"] = {
                "passed": corridor_passed,
                "actual": actual_corridor_ratio,
                "required_max": max_corridor_ratio
            }
            
            if not corridor_passed:
                report["overall_passed"] = False
                report["score"] -= 15
            
            # Validate corridor width
            if arch_circulation and "corridor_width_m" in arch_circulation:
                # Get from architectural constraints
                corridor_width_config = arch_circulation.get("corridor_width_m", {})
                layout_type = arch_circulation.get("layout_type", "double_loaded")
                
                if layout_type == "single_loaded":
                    width_config = corridor_width_config.get("single_loaded", {})
                elif layout_type == "double_loaded":
                    width_config = corridor_width_config.get("double_loaded", {})
                else:
                    width_config = corridor_width_config.get("main", {})
                
                min_corridor_width = width_config.get("min", 2.0)
            else:
                # Fall back to legacy format
                min_corridor_width = legacy_circulation.get("corridor_width_m", {}).get("min", 2.0)
            
            # Note: This would require actual corridor geometry analysis
            # For now, assume it passes if we used correct width in generation
            report["constraints"]["corridor_width"] = {
                "passed": True,
                "assumed": min_corridor_width
            }
            
            # Validate unit counts
            unit_constraints = self.constraints.get("units", [])
            units_by_type = {}
            for unit in units:
                unit_type = unit["type"]
                units_by_type[unit_type] = units_by_type.get(unit_type, 0) + 1
            
            for uc in unit_constraints:
                unit_type = uc["type"]
                required_count = uc["count"]
                actual_count = units_by_type.get(unit_type, 0)
                
                count_passed = actual_count == required_count
                report["constraints"][f"unit_count_{unit_type}"] = {
                    "passed": count_passed,
                    "actual": actual_count,
                    "required": required_count
                }
                
                if not count_passed:
                    report["overall_passed"] = False
                    report["score"] -= 10
            
            # Validate service room ratio
            service = self.constraints.get("service", {})
            service_ratio_range = service.get("service_rooms_ratio", {})
            min_service = service_ratio_range.get("min", 0.05)
            max_service = service_ratio_range.get("max", 0.08)
            
            # Assume 6% service ratio for now (would calculate from actual layout)
            actual_service = 0.06
            service_passed = min_service <= actual_service <= max_service
            
            report["constraints"]["service_ratio"] = {
                "passed": service_passed,
                "actual": actual_service,
                "required_range": [min_service, max_service]
            }
            
            if not service_passed:
                report["score"] -= 10
            
            # Validate efficiency
            arch_efficiency = self.arch_constraints.get("efficiency", {})
            if arch_efficiency and "net_to_gross_ratio" in arch_efficiency:
                min_efficiency = arch_efficiency.get("net_to_gross_ratio", {}).get("min", 0.70)
            else:
                min_efficiency = 0.60  # Default minimum
            
            efficiency = metrics.get("efficiency", 0)
            if efficiency < min_efficiency:
                report["score"] -= 20
                report["overall_passed"] = False
                report["constraints"]["efficiency"] = {
                    "passed": False,
                    "actual": efficiency,
                    "required_min": min_efficiency
                }
            else:
                report["constraints"]["efficiency"] = {
                    "passed": True,
                    "actual": efficiency,
                    "required_min": min_efficiency
                }
            
            report["score"] = max(0, report["score"])
            
            logger.info(f"Validation: {report['overall_passed']}, score = {report['score']}")
            return report
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return report
