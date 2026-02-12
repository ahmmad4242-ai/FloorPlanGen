# FloorPlanGen V2.5.1 - Production Release

## 📋 Project Overview

**FloorPlanGen** is an intelligent floor plan generation engine that creates architectural layouts with proper corridors, units, and cores. Built with Python, Shapely, and advanced geometric algorithms.

**Current Version**: V2.5.1 (Production)  
**Release Date**: 2026-01-30  
**Status**: ✅ Stable & Deployed

---

## 🎯 Features (V2.5.1)

### ✅ Core Capabilities

**⚠️ IMPORTANT**: Parameters go inside `constraints.architectural_constraints`:
- `corridor_pattern` → `constraints.architectural_constraints.circulation.corridor_pattern`
- `core_count` → `constraints.architectural_constraints.core.core_count`

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for full examples.

1. **Multi-Core Support**
   - 1 Core: Single central core (default)
   - 2 Cores: Two cores at optimal positions
   - 4 Cores: Four cores in corners
   - Automatic positioning and sizing

2. **Advanced Corridor Patterns**
   - **Grid Pattern**: 2×2 or 3×3 grid layout (NEW in V2.5.1)
   - **H-Pattern**: Double-loaded with cross corridor
   - **U-Pattern**: 3-sided perimeter corridor
   - **L-Pattern**: Two perpendicular corridors
   - **Plus (+)**: 4-directional from center
   - **T-Pattern**: Main spine + branch
   - **Line Pattern**: Single straight corridor
   - **Auto**: Intelligent pattern selection

3. **Professional Unit Placement**
   - Multi-pass placement (4 passes with adaptive constraints)
   - Corridor-connected units (all units have corridor access)
   - Perimeter-facing units (for natural light)
   - Mixed unit types (Studio, 1BR, 2BR, 3BR)
   - Adaptive grid sampling for optimal space utilization

4. **API Support**
   - `/generate` endpoint with full JSON API
   - `corridor_pattern` parameter for manual selection
   - `core_count` parameter (1, 2, or 4)
   - Unit constraints and distribution control

---

## 📊 Performance Metrics (V2.5.1)

### Space Allocation
```
Boundary:       3024 m² (100%)
Core:             40 m² (1.3%)
Corridors:       286 m² (9.5%)
Units:          1684 m² (55.7%)
Total Used:     2010 m² (66.5%)
Wasted:         1014 m² (33.5%)
```

### Unit Distribution
```
Total Units:    38 units
  - 1BR:        15 units (39.5%)
  - 2BR:        11 units (28.9%)
  - 3BR:         4 units (10.5%)
  - Studio:      8 units (21.1%)
```

### Generation Time
```
Average:        ~10 seconds
Typical Range:   8-15 seconds
```

---

## 🚀 API Usage

### Generate Floor Plan

**Endpoint**: `POST /generate`

**⚠️ IMPORTANT**: `corridor_pattern` and `core_count` go inside `constraints.architectural_constraints`

**Request Example**:
```json
{
  "project_id": "test-2026-01-30",
  "dxf_url": "https://example.com/floor.dxf",
  "boundary_layer": "BOUNDARY",
  "variant_count": 5,
  "constraints": {
    "architectural_constraints": {
      "core": {
        "core_count": 1,
        "elevators": 2,
        "stairs": 2,
        "net_area_m2": {"min": 30, "target": 40, "max": 50}
      },
      "circulation": {
        "corridor_pattern": "grid",
        "corridor_width_m": {"min": 2.0, "target": 2.2, "max": 2.5},
        "corridor_area_ratio": {"min": 0.08, "target": 0.10, "max": 0.15}
      },
      "units": [
        {
          "type": "Studio",
          "percentage": 20,
          "net_area_m2": {"min": 25, "target": 30, "max": 35}
        },
        {
          "type": "1BR",
          "percentage": 40,
          "net_area_m2": {"min": 45, "target": 55, "max": 65}
        },
        {
          "type": "2BR",
          "percentage": 30,
          "net_area_m2": {"min": 65, "target": 75, "max": 85}
        },
        {
          "type": "3BR",
          "percentage": 10,
          "net_area_m2": {"min": 85, "target": 100, "max": 115}
        }
      ]
    }
  }
}
```

**Corridor Pattern Options**:
- `"grid"` - 2×2 or 3×3 intersecting corridors (12-16% area)
- `"H"` - Double-loaded with cross (9-11% area) ⭐ Recommended for large buildings
- `"U"` - 3-sided perimeter (10-12% area)
- `"L"` - Two perpendicular corridors (8-10% area)
- `"+"` - 4-directional from center (9-11% area)
- `"T"` - Main spine + branch (8-10% area)
- `"line"` - Single straight corridor (6-8% area)
- `"auto"` - Intelligent selection (default)

**Core Count Options**:
- `1` - Single central core (default, for buildings < 2000 m²)
- `2` - Dual cores at both ends (for elongated buildings 2000-4000 m²)
- `4` - Quad cores at corners (for large buildings > 4000 m²)

**📖 Full API Documentation**: See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

### Old Request Format (DEPRECATED)
```json
{
  "project_id": "test-2026-01-30",
  "boundary": {
    "coordinates": [[0,0], [63,0], [63,48], [0,48], [0,0]]
  },
  "corridor_pattern": "grid",
  "core_count": 1,
  "unit_constraints": {
    "generation_strategy": "fill_available",
    "units": [...]
  }
}
```
⚠️ This format is DEPRECATED. Use `architectural_constraints` instead.

**Response Example**:
      {
        "type": "Studio",
        "percentage": 20,
        "area": {"min": 25, "target": 30, "max": 35}
      },
      {
        "type": "1BR",
        "percentage": 40,
        "area": {"min": 45, "target": 55, "max": 65}
      },
      {
        "type": "2BR",
        "percentage": 30,
        "area": {"min": 65, "target": 75, "max": 85}
      },
      {
        "type": "3BR",
        "percentage": 10,
        "area": {"min": 85, "target": 100, "max": 115}
      }
    ]
  }
}
```

**Response Example**:
```json
{
  "job_id": "uuid-abc123",
  "status": "completed",
  "message": "Generated 5 variants successfully",
  "variants": [
    {
      "variant_id": "uuid-variant-1",
      "variant_number": 1,
      "metrics": {
        "total_area": 3024.0,
        "core_area": 40.0,
        "corridor_area": 286.3,
        "units_area": 1684.1,
        "efficiency": 0.665,
        "corridor_ratio": 0.095,
        "units_count": 38
      },
      "units_by_type": {
        "Studio": 8,
        "1BR": 15,
        "2BR": 11,
        "3BR": 4
      },
      "cores": [
        {
          "id": "core_1",
          "area_m2": 40.0,
          "centroid": [31.5, 24.0]
        }
      ]
      },
      "corridors": {
        "pattern": "grid",
        "segment_count": 3,
        "total_area_m2": 286.3
      },
      "dxf_download_url": "/variant/uuid-variant-1/download",
      "svg_preview_url": "/variant/uuid-variant-1/preview"
    }
  ]
}
```

---

## 🏗️ Architecture

### Technology Stack
- **Backend**: Python 3.12+
- **Geometry**: Shapely 2.0+
- **Web**: FastAPI / Hono (hybrid)
- **Deployment**: Cloudflare Pages (edge)

### Project Structure
```
webapp/
├── app/
│   ├── professional_layout_engine.py  # Main layout engine
│   ├── corridor_patterns.py           # Corridor generators
│   ├── multi_core_support.py          # Multi-core placement
│   └── row_based_layout_v3_1.py       # Experimental V3.1
├── public/
│   └── static/                        # Frontend assets
├── test_*.py                           # Test scripts
├── README.md                           # This file
└── wrangler.jsonc                     # Cloudflare config
```

---

## 🧪 Testing

### Run Local Tests
```bash
# Test V2.5.1 with default settings
python3 test_v2.6.0_ultimate_fill.py

# Test with specific pattern
python3 test_pattern.py --pattern grid

# Test with multi-core
python3 test_cores.py --core_count 4
```

### Expected Results
- **Coverage**: 66-77% (target: 95%+, achieved: 66-77%)
- **Units**: 33-38 units (varies by boundary size)
- **Corridors**: 9-10% of total area (architectural standard)
- **Generation Time**: <15 seconds

---

## 📈 Development Roadmap

### V2.5.1 (Current - STABLE)
- ✅ Grid Pattern (2×2, 3×3)
- ✅ Multi-Core Support (1, 2, 4)
- ✅ Manual Pattern Selection
- ✅ API Integration
- ✅ Coverage: 66-77%

### V3.0 (Future - Research Phase)
- 🔬 Row-Based Layout Algorithm
- 🔬 95%+ Coverage Target
- 🔬 ETA: 1-2 weeks
- ⚠️ Status: Experimental (V3.0 and V3.1 experiments showed no improvement)

**Note**: V3.0 experiments (row-based layout) did not improve coverage:
- V3.0: 19.9% coverage (worse than V2.5.1)
- V3.1: 55.6% coverage (still worse than V2.5.1)
- Decision: Keep V2.5.1 as production version

---

## 🔧 Known Limitations

1. **Coverage**: Currently 66-77%, target is 95%+
   - Wasted space: ~28-34%
   - Root cause: region.difference() creates fragmented areas

2. **Corridors**: Grid pattern uses more area (16%) than optimal (9-10%)
   - Auto pattern (H/U/L) is more efficient

3. **Unit Count**: 33-38 units for 3024 m² boundary
   - Target: 45-50 units (requires better space utilization)

4. **Generation Time**: ~10 seconds average
   - Acceptable for current use case
   - Could be optimized further

---

## 🎓 Algorithm Details

### Multi-Pass Placement Strategy

**Pass 1 (Strict)**:
- Min perimeter: 0.8m
- Max corridor distance: 0.5m
- Min area match: 50%
- Max attempts: 300

**Pass 2 (Relaxed)**:
- Min perimeter: 0.0m
- Max corridor distance: 5.0m
- Min area match: 35%
- Max attempts: 500

**Pass 3 (Flexible)**:
- Min perimeter: 0.0m
- Max corridor distance: 15.0m
- Min area match: 25%
- Max attempts: 1500

**Pass 4 (Gap Filling)**:
- Min area match: 20%
- Max attempts: 2000
- Ultra-fine grid: 0.2m spacing

### Adaptive Grid Sampling

- **Tiny regions** (<100 m²): 0.15× unit size steps
- **Medium regions** (100-500 m²): 0.20× unit size steps
- **Large regions** (>500 m²): 0.25× unit size steps

---

## 🐛 Troubleshooting

### Low Coverage (<60%)
- Try different corridor patterns: `H`, `U`, or `+`
- Reduce core count to 1
- Check boundary complexity (simpler is better)

### Too Many Corridors (>12%)
- Use `auto` pattern instead of `grid`
- Larger boundaries work better with grid

### Generation Timeout
- Reduce boundary size
- Simplify polygon (fewer vertices)
- Use fewer unit types

---

## 📦 Deployment

### GitHub Repository
```bash
git clone <repository-url>
cd webapp
npm install
npm run build
```

### Cloudflare Pages
```bash
# Deploy to production
npm run deploy:prod

# Or use wrangler directly
npx wrangler pages deploy dist --project-name webapp
```

---

## 📝 Version History

### V2.5.1 (2026-01-30) - Current
- ✅ Grid Pattern complete
- ✅ Multi-Core (1/2/4) support
- ✅ Manual pattern selection
- ✅ API integration
- ✅ Coverage: 66-77%

### V2.5.0 (2026-01-29)
- Initial Grid Pattern implementation
- Multi-Core foundation

### V2.4.3 (2026-01-28)
- Baseline: 66% coverage
- Region-based placement

### V2.0.0 (2026-01-27)
- First production release
- Basic corridor patterns

---

## 📧 Contact & Support

**Project**: FloorPlanGen  
**Version**: V2.5.1  
**Status**: Production  
**License**: MIT  

**Links**:
- **GitHub**: https://github.com/ahmmad4242-ai/FloorPlanGen
- **Backup Archive**: https://www.genspark.ai/api/files/s/KQ3BLZ1X (87MB)
- **Release Date**: 2026-01-30

---

**Built with ❤️ using Python, Shapely, FastAPI, and Cloudflare Pages**
