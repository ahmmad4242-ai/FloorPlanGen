# 🐍 FloorPlanGen - Python Generator Service

## Overview
Real floor plan generation engine using Python, ezdxf, Shapely, and OR-Tools CP-SAT.

## Features

### ✅ DXF Reading
- Extract boundaries from BOUNDARY layer
- Extract obstacles (columns, voids, no-build zones)
- Extract fixed elements (cores, stairs, elevators)
- Support for LWPOLYLINE, POLYLINE, CIRCLE, INSERT entities

### ✅ Space Partitioning
- Core placement (center, north, south, east, west)
- Corridor network generation (double-loaded, single-loaded, circular)
- Unit partitioning with grid-based algorithm
- Usable area calculation (boundary - obstacles)

### ✅ Constraint Solving
- OR-Tools CP-SAT optimizer
- Unit count and area constraints
- Corridor ratio validation
- Service room ratio validation
- Efficiency scoring

### ✅ DXF Export
- Organized layers (BOUNDARY, WALLS, DOORS, CORRIDORS, CORE, UNITS, TEXT, DIMENSIONS)
- Hatching for cores
- Unit labels with type and area
- Wall thickness
- Title block with project info

## Tech Stack

- **FastAPI**: Modern Python web framework
- **ezdxf**: DXF file reading/writing
- **Shapely**: Geometric operations
- **OR-Tools**: Constraint programming solver
- **NumPy**: Numerical operations

## Installation

### Using Docker (Recommended)

```bash
# Build image
docker build -t floorplangen-generator ./generator-service

# Run container
docker run -p 8001:8001 floorplangen-generator
```

### Using Docker Compose

```bash
# Start all services (Backend + Generator)
docker-compose up -d

# View logs
docker-compose logs -f generator

# Stop services
docker-compose down
```

### Manual Installation

```bash
cd generator-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run service
python -m app.main
```

## API Endpoints

### Health Check
```bash
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "FloorPlanGen Generator Service",
  "version": "1.0.0",
  "dependencies": {
    "ezdxf": "✓",
    "shapely": "✓",
    "ortools": "✓"
  }
}
```

### Generate Floor Plans
```bash
POST /generate
Content-Type: application/json
```

**Request Body**:
```json
{
  "project_id": "proj-xxx",
  "dxf_file_path": "/path/to/floor.dxf",
  "boundary_layer": "BOUNDARY",
  "constraints": {
    "units": [
      {
        "type": "1BR",
        "count": 10,
        "net_area_m2": { "min": 55, "max": 70 }
      }
    ],
    "circulation": {
      "corridor_width_m": { "min": 2.0, "target": 2.2 },
      "corridor_area_ratio": { "max": 0.18 }
    },
    "core": {
      "elevators": 3,
      "stairs": 2,
      "preferred_zones": ["center"]
    }
  },
  "variant_count": 5
}
```

**Response**:
```json
{
  "job_id": "job-abc123",
  "status": "completed",
  "message": "Generated 5 variants successfully"
}
```

### Download Variant DXF
```bash
GET /variant/{variant_id}/download
```

**Response**: DXF file download

## Architecture

### Module Structure

```
generator-service/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application
│   ├── dxf_reader.py           # DXF file parsing
│   ├── space_partition.py      # Space partitioning algorithm
│   ├── constraint_solver.py    # OR-Tools constraint solver
│   └── dxf_exporter.py         # DXF file generation
├── requirements.txt
├── Dockerfile
└── README.md
```

### Generation Flow

```
1. DXF Reading
   └─> Extract boundary polygon
   └─> Extract obstacles (columns, voids)
   └─> Extract fixed elements (cores, stairs)

2. Space Partitioning
   └─> Calculate usable area (boundary - obstacles)
   └─> Place core (center, north, south, etc.)
   └─> Create corridor network (double-loaded, etc.)
   └─> Partition into units (grid-based algorithm)

3. Constraint Solving
   └─> Validate unit counts and areas
   └─> Check corridor ratio
   └─> Verify service room ratio
   └─> Calculate compliance score

4. DXF Export
   └─> Create organized layers
   └─> Add boundary, core, corridors, units
   └─> Add walls with thickness
   └─> Add labels and dimensions
   └─> Generate title block
```

## Configuration

### Environment Variables

```bash
# Python logging level
LOG_LEVEL=INFO

# Temp directory for generated files
TEMP_DIR=/tmp/floorplangen

# Service port
PORT=8001
```

## Testing

### Manual Test with Sample DXF

```bash
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "test-001",
    "boundary_layer": "BOUNDARY",
    "constraints": {
      "units": [
        {"type": "1BR", "count": 8, "net_area_m2": {"min": 55, "max": 70}}
      ],
      "circulation": {
        "corridor_width_m": {"min": 2.0, "target": 2.2},
        "corridor_area_ratio": {"max": 0.18}
      },
      "core": {
        "elevators": 2,
        "stairs": 2,
        "preferred_zones": ["center"]
      }
    },
    "variant_count": 3
  }'
```

### Health Check

```bash
curl http://localhost:8001/health
```

## Performance

### Generation Times (Typical)

- **Simple floor (10 units)**: ~2-5 seconds
- **Medium floor (20 units)**: ~5-10 seconds
- **Complex floor (40 units)**: ~10-20 seconds

### Resource Usage

- **Memory**: ~200-500 MB per generation
- **CPU**: 1-2 cores utilized during generation

## Known Limitations

1. **Grid-Based Partitioning**: Current algorithm uses simple grid. More sophisticated algorithms (recursive subdivision, L-systems) could improve results.

2. **Fixed Core Size**: Core size is calculated from area but not optimized based on actual elevator/stair requirements.

3. **Simplified Corridor Network**: Double-loaded corridor is basic rectangular. More complex topologies (circular, L-shaped) are partially implemented.

4. **OR-Tools Integration**: Currently validates constraints post-generation. Could be integrated earlier in the partitioning phase for better optimization.

5. **DXF Layers**: Exported DXF has standard layers but doesn't include doors, windows, or furniture yet.

## Future Enhancements

### Phase 3 Improvements

1. **Advanced Partitioning**:
   - Recursive space subdivision
   - L-system based generation
   - Genetic algorithms for optimization

2. **Detailed Elements**:
   - Door placement algorithm
   - Window placement based on facade
   - Furniture layout generation

3. **3D Export**:
   - Generate 3D models (IFC format)
   - Height extrusion for walls
   - Roof and floor slabs

4. **Optimization**:
   - Multi-objective optimization (area + view + sunlight)
   - Pareto frontier generation
   - Interactive refinement

5. **AI Integration**:
   - ML-based unit layout prediction
   - Style transfer from reference projects
   - Generative adversarial networks

## Troubleshooting

### Service Won't Start

```bash
# Check Python version (requires 3.11+)
python --version

# Check dependencies
pip list | grep -E "ezdxf|shapely|ortools"

# View logs
docker-compose logs generator
```

### DXF Generation Fails

- **Check DXF file format**: Must be R2010 or later
- **Verify boundary layer**: Ensure BOUNDARY layer exists with closed polyline
- **Check coordinates**: Ensure coordinates are in meters, not millimeters

### Performance Issues

- Reduce `variant_count` (try 3-5 instead of 10-50)
- Simplify DXF input (remove unnecessary details)
- Increase Docker container resources

## Contributing

Contributions welcome! Areas for improvement:

1. Better space partitioning algorithms
2. More sophisticated constraint solving
3. Richer DXF export (doors, windows, furniture)
4. Performance optimization
5. Unit tests

## License

MIT License - See LICENSE file

## Contact

- **Project**: FloorPlanGen
- **Version**: 1.0.0
- **Docs**: See main README.md

---

**Built with ❤️ using Python, FastAPI, ezdxf, Shapely, and OR-Tools**
