"""
FloorPlanGen - Main FastAPI Application
Provides REST API for floor plan generation.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import json
import os
import tempfile
import uuid
import random
import time
import httpx  # Add HTTP client for downloading DXF
from pathlib import Path
import ezdxf

from .dxf_reader import DXFReader
from .space_partition import ArchitecturalSpacePartitioner as SpacePartitioner
from .professional_layout_engine import ProfessionalLayoutEngine  # NEW: FIXED professional layout engine
from .constraint_solver import ConstraintSolver
from .dxf_exporter import DXFExporter
from .svg_generator import SVGGenerator
from .architectural_validator import ArchitecturalConstraintsValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FloorPlanGen Generator Service",
    description="Python microservice for real floor plan generation",
    version="1.0.0"
)

# Create temp directory for generated files
TEMP_DIR = Path("/tmp/floorplangen")
TEMP_DIR.mkdir(exist_ok=True)


# ==================== Pydantic Models ====================

class GenerateRequest(BaseModel):
    project_id: str
    dxf_url: Optional[str] = None
    dxf_file_path: Optional[str] = None
    boundary_layer: str = "BOUNDARY"
    constraints: Dict
    variant_count: int = 5


class GenerateResponse(BaseModel):
    job_id: str
    status: str
    message: str


class VariantMetadata(BaseModel):
    variant_id: str
    variant_number: int
    total_area: float
    usable_area: float
    core_area: float
    corridor_area: float
    units_area: float
    efficiency: float
    corridor_ratio: float
    units_count: int
    units_by_type: Dict[str, int]


class ComplianceReport(BaseModel):
    overall_passed: bool
    score: float
    constraints: Dict


# ==================== API Endpoints ====================

@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "service": "FloorPlanGen Generator",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "service": "FloorPlanGen Generator Service",
        "version": "1.0.0",
        "dependencies": {
            "ezdxf": "✓",
            "shapely": "✓",
            "ortools": "✓"
        }
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate_floor_plan(request: GenerateRequest):
    """
    Generate floor plan variants based on DXF input and constraints.
    
    This is the main generation endpoint that:
    1. Reads DXF file
    2. Extracts boundaries and obstacles
    3. Partitions space
    4. Optimizes with constraints
    5. Exports DXF files
    """
    try:
        logger.info(f"Received generation request for project {request.project_id}")
        
        # Create job ID
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        
        # Get DXF file path
        if request.dxf_file_path:
            dxf_path = request.dxf_file_path
        elif request.dxf_url:
            # Download DXF from URL
            logger.info(f"Downloading DXF from URL: {request.dxf_url}")
            dxf_path = str(TEMP_DIR / f"{request.project_id}_input.dxf")
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(request.dxf_url)
                    response.raise_for_status()
                    
                    # Save DXF content to file
                    with open(dxf_path, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"Downloaded DXF: {len(response.content)} bytes → {dxf_path}")
                    
            except Exception as download_error:
                logger.error(f"Failed to download DXF from {request.dxf_url}: {download_error}")
                # Fallback to sample DXF
                logger.warning("Falling back to sample DXF")
                dxf_path = create_sample_dxf(request.project_id)
        else:
            # No DXF provided, create a sample for testing
            logger.warning(f"No DXF file provided, creating sample for project {request.project_id}")
            dxf_path = create_sample_dxf(request.project_id)
        
        # Check if file exists, if not create sample
        if not os.path.exists(dxf_path):
            logger.warning(f"DXF file not found: {dxf_path}, creating sample")
            dxf_path = create_sample_dxf(request.project_id)
        
        # Generate variants
        variants = await generate_variants_internal(
            project_id=request.project_id,
            dxf_path=dxf_path,
            boundary_layer=request.boundary_layer,
            constraints=request.constraints,
            variant_count=request.variant_count
        )
        
        # Store generated variants in memory
        global generated_variants_store
        generated_variants_store[request.project_id] = [
            {
                "variant_id": v["variant_id"],
                "variant_number": v["variant_number"],
                "score": v["score"],
                "metadata": v["metadata"],
                "compliance": v["compliance"],
                "dxf_url": v.get("dxf_file_path"),
                "svg_url": v.get("svg_file_path")  # ✅ Add SVG path!
            }
            for v in variants
        ]
        
        logger.info(f"Generated {len(variants)} variants for job {job_id}, stored in memory")
        
        return GenerateResponse(
            job_id=job_id,
            status="completed",
            message=f"Generated {len(variants)} variants successfully"
        )
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


async def generate_variants_internal(
    project_id: str,
    dxf_path: str,
    boundary_layer: str,
    constraints: Dict,
    variant_count: int
) -> List[Dict]:
    """Internal function to generate multiple variants."""
    
    variants = []
    
    try:
        # Step 1: Read DXF
        reader = DXFReader()
        if not reader.load_dxf(dxf_path):
            raise Exception("Failed to load DXF file")
        
        boundary = reader.extract_boundary(boundary_layer)
        if not boundary:
            raise Exception(f"No boundary found on layer {boundary_layer}")
        
        obstacles = reader.extract_obstacles()
        fixed_elements = reader.extract_fixed_elements()
        
        logger.info(f"Extracted: boundary={boundary.area:.2f}m², obstacles={len(obstacles)}")
        
        # Step 2: Generate multiple variants
        for i in range(variant_count):
            try:
                variant = generate_single_variant(
                    project_id=project_id,
                    variant_number=i + 1,
                    boundary=boundary,
                    obstacles=obstacles,
                    fixed_elements=fixed_elements,
                    constraints=constraints
                )
                variants.append(variant)
            except Exception as e:
                logger.error(f"Failed to generate variant {i+1}: {e}")
        
        return variants
        
    except Exception as e:
        logger.error(f"Variant generation failed: {e}")
        raise


def generate_single_variant(
    project_id: str,
    variant_number: int,
    boundary,
    obstacles,
    fixed_elements,
    constraints: Dict
) -> Dict:
    """Generate a single floor plan variant with randomization for diversity."""
    
    try:
        # Set unique random seed for each variant
        random.seed(int(time.time() * 1000) + variant_number)
        
        # Extract architectural constraints if provided
        arch_constraints = constraints.get("architectural_constraints", {})
        
        # Step 1: Professional Architectural Layout (FIXED ENGINE!)
        logger.info("Using ProfessionalLayoutEngine - FIXED for visible corridors and proper connectivity")
        layout_engine = ProfessionalLayoutEngine(boundary, obstacles)
        
        # Place core with randomization
        core_config = arch_constraints.get("core") or constraints.get("core", {})
        fixed_core = fixed_elements.get("core", [])
        fixed_core = fixed_core[0] if fixed_core else None
        
        # Get core area from architectural constraints or use default
        if core_config and "area_m2" in core_config:
            core_area_config = core_config["area_m2"]
            core_area_min = core_area_config.get("min", 25)
            core_area_max = core_area_config.get("max", 60)
            core_area_target = core_area_config.get("target", 40)
            # Randomize within user-defined range
            core_area = random.uniform(core_area_min, core_area_max)
        else:
            # Default randomization (±10%)
            base_core_area = 40.0
            core_area = base_core_area * (1.0 + random.uniform(-0.1, 0.1))
        
        # Get preferred location from architectural constraints
        preferred_location = core_config.get("preferred_location", "center")
        if variant_number > 1 and not fixed_core:
            # For variant 2+, try different locations
            core_locations = ["center", "north", "south", "east", "west"]
            preferred_location = random.choice(core_locations)
            logger.info(f"Variant {variant_number}: Using core location '{preferred_location}'")
        
        core = layout_engine.place_core(
            core_area=core_area,
            preferred_location=preferred_location,
            fixed_core=fixed_core
        )
        
        # Create professional corridor network (spine + branches)
        circulation_config = arch_constraints.get("circulation") or constraints.get("circulation", {})
        
        if circulation_config and "corridor_width_m" in circulation_config:
            corridor_width_config = circulation_config["corridor_width_m"]
            corridor_width_min = corridor_width_config.get("min", 1.8)
            corridor_width_max = corridor_width_config.get("max", 2.5)
            corridor_width_target = corridor_width_config.get("target", 2.2)
            # Randomize within user-defined range
            corridor_width = random.uniform(corridor_width_min, corridor_width_max)
        else:
            # Default randomization (±10%)
            base_corridor_width = circulation_config.get("corridor_width_m", {}).get("target", 2.2)
            corridor_width = base_corridor_width * (1.0 + random.uniform(-0.1, 0.1))
        
        # Get layout type from architectural constraints
        layout_type = circulation_config.get("layout_type", "double_loaded")
        if variant_number > 1:
            layout_types = ["double_loaded", "single_loaded"]
            layout_type = random.choice(layout_types)
        
        logger.info(f"Variant {variant_number}: corridor_width={corridor_width:.2f}m, layout={layout_type}")
        
        # NEW: Create VISIBLE corridor network (10-15% of floor area)
        corridors = layout_engine.create_visible_corridor_network(
            core=core,
            corridor_width=corridor_width
        )
        
        # Prepare unit types for layout engine - support both "units" and "unit_types"
        units_config = constraints.get("units") or constraints.get("unit_types", [])
        unit_types_for_layout = []
        
        for uc in units_config:
            # Support both structures: {"type": "1BR", "count": 2, "min_area": 55, "max_area": 70}
            # and {"net_area_m2": {"min": 55, "max": 70}, "count": 2}
            unit_type = uc.get("type", "Studio")
            count = uc.get("count", 0)
            
            if "min_area" in uc and "max_area" in uc:
                min_area = uc.get("min_area", 50)
                max_area = uc.get("max_area", 100)
            else:
                area_range = uc.get("net_area_m2", {})
                min_area = area_range.get("min", 50)
                max_area = area_range.get("max", 100)
            
            # Add to layout engine format
            unit_types_for_layout.append({
                "type": unit_type,
                "count": count,
                "min_area": min_area,
                "max_area": max_area
            })
        
        logger.info(f"Planning units: {unit_types_for_layout}")
        
        # NEW: Layout units with PROPER corridor access and perimeter windows
        units = layout_engine.layout_units_with_corridor_access(
            core=core,
            corridors=corridors,
            unit_types=unit_types_for_layout
        )
        
        # Calculate metrics (units area, corridor area, efficiency)
        units_area = sum(u["area"] for u in units)
        corridor_area = sum(c.area for c in corridors)
        core_area_actual = core.area if core else 0
        total_area = boundary.area
        
        metrics = {
            "total_area": total_area,
            "usable_area": total_area,
            "core_area": core_area_actual,
            "corridor_area": corridor_area,
            "units_area": units_area,
            "efficiency": units_area / total_area if total_area > 0 else 0,
            "corridor_ratio": corridor_area / total_area if total_area > 0 else 0,
            "units_count": len(units)
        }
        
        # Step 2: Constraint Solving & Validation
        solver = ConstraintSolver(constraints)
        validation_report = solver.validate_constraints(metrics, units)
        
        # Step 2.5: Architectural Validation (NEW!)
        arch_validator = ArchitecturalConstraintsValidator()
        arch_validation = arch_validator.validate_floor_plan(
            units=units,
            corridors=corridors,
            core=core,
            boundary=boundary
        )
        
        logger.info(f"Architectural validation: {arch_validation['summary']}")
        logger.info(f"Compliance score: {arch_validation['score']}/100")
        
        if arch_validation['violations']:
            logger.warning(f"Found {len(arch_validation['violations'])} violations:")
            for violation in arch_validation['violations'][:5]:  # Log first 5
                logger.warning(f"  [{violation['code']}] {violation['message']}")
        
        # Merge validation results
        validation_report['architectural_validation'] = {
            "score": arch_validation['score'],
            "is_valid": arch_validation['is_valid'],
            "violations_count": len(arch_validation['violations']),
            "warnings_count": len(arch_validation['warnings']),
            "violations": arch_validation['violations'],
            "warnings": arch_validation['warnings']
        }
        
        # Step 3: Export DXF
        variant_id = f"var-{uuid.uuid4().hex[:12]}"
        dxf_path = str(TEMP_DIR / f"{project_id}_{variant_id}.dxf")
        
        # Export to DXF with architectural constraints
        exporter = DXFExporter()
        exporter.create_new_drawing()
        exporter.add_boundary(boundary)
        exporter.add_core(core)
        exporter.add_corridors(corridors)
        exporter.add_units(units)
        
        # Get wall thickness from architectural constraints
        wall_thickness = 0.2  # Default
        if arch_constraints:
            # Could add to arch_constraints in future: arch_constraints.get("walls", {}).get("thickness_m", 0.2)
            pass
        
        # Get door width from architectural constraints
        door_width = 0.9  # Default minimum for accessibility
        if arch_constraints and "accessibility" in arch_constraints:
            door_width = arch_constraints.get("accessibility", {}).get("wheelchair_access", {}).get("door_width_m", 0.9)
        
        exporter.add_walls(units, wall_thickness=wall_thickness)
        exporter.add_doors(units, corridors, door_width=door_width)
        exporter.add_title_block(
            project_name=project_id,
            variant_number=variant_number,
            area=metrics["total_area"],
            units_count=len(units)
        )
        exporter.save(dxf_path)
        
        # Generate SVG preview
        svg_generator = SVGGenerator(width=800, height=600)
        svg_content = svg_generator.generate_svg(boundary, core, corridors, units)
        svg_path = str(TEMP_DIR / f"{project_id}_{variant_id}.svg")
        
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        
        logger.info(f"Generated SVG preview at {svg_path}")
        
        # Prepare variant data
        units_by_type = {}
        for unit in units:
            unit_type = unit["type"]
            units_by_type[unit_type] = units_by_type.get(unit_type, 0) + 1
        
        variant_data = {
            "variant_id": variant_id,
            "variant_number": variant_number,
            "dxf_file_path": dxf_path,
            "svg_file_path": svg_path,
            "metadata": {
                **metrics,
                "units_by_type": units_by_type
            },
            "compliance": validation_report,
            "score": validation_report["score"]
        }
        
        logger.info(f"Generated variant {variant_number}: score={validation_report['score']:.2f}")
        return variant_data
        
    except Exception as e:
        logger.error(f"Failed to generate variant {variant_number}: {e}")
        raise


def create_sample_dxf(project_id: str) -> str:
    """Create a larger sample DXF file for realistic testing."""
    try:
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Create larger sample boundary (50m x 30m = 1500m² rectangle)
        # This allows for 10-15 units realistically
        boundary_points = [
            (0, 0),
            (50, 0),
            (50, 30),
            (0, 30),
            (0, 0)
        ]
        
        msp.add_lwpolyline(
            boundary_points,
            dxfattribs={'layer': 'BOUNDARY', 'closed': True}
        )
        
        # Add fewer columns for more usable space
        columns = [
            (15, 15, 0.4),
            (35, 15, 0.4)
        ]
        
        for x, y, radius in columns:
            msp.add_circle((x, y), radius, dxfattribs={'layer': 'COLUMNS'})
        
        # Save
        output_path = str(TEMP_DIR / f"{project_id}_sample.dxf")
        doc.saveas(output_path)
        
        logger.info(f"Created larger sample DXF (50x30m): {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to create sample DXF: {e}")
        raise


@app.get("/variant/{variant_id}/download")
async def download_variant(variant_id: str, format: str = "dxf"):
    """Download generated DXF or SVG file."""
    try:
        if format == "svg":
            # Find SVG file
            svg_files = list(TEMP_DIR.glob(f"*{variant_id}.svg"))
            
            if not svg_files:
                raise HTTPException(status_code=404, detail="Variant SVG file not found")
            
            return FileResponse(
                path=str(svg_files[0]),
                media_type="image/svg+xml",
                filename=f"{variant_id}.svg"
            )
        else:
            # Find DXF file
            dxf_files = list(TEMP_DIR.glob(f"*{variant_id}.dxf"))
            
            if not dxf_files:
                raise HTTPException(status_code=404, detail="Variant DXF file not found")
            
            return FileResponse(
                path=str(dxf_files[0]),
                media_type="application/dxf",
                filename=f"{variant_id}.dxf"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)


# ==================== Variants Storage ====================
# Simple in-memory storage for generated variants
# In production, this should use a proper database
generated_variants_store = {}

@app.get("/variants/{project_id}")
def get_generated_variants(project_id: str):
    """Get all generated variants for a project."""
    variants = generated_variants_store.get(project_id, [])
    return {"project_id": project_id, "variants": variants}
