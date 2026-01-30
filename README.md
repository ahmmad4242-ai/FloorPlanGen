# FloorPlanGen V2.5.1 - Production Release

## 📋 Project Overview

**FloorPlanGen** is an intelligent floor plan generation engine that creates architectural layouts with proper corridors, units, and cores. Built with Python, Shapely, and advanced geometric algorithms.

**Current Version**: V2.5.1 (Production)  
**Release Date**: 2026-01-30  
**Status**: ✅ Stable & Deployed

---

## 🎯 Features (V2.5.1)

### ✅ Core Capabilities

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

**Request Example**:
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
    "units": [
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
  "project_id": "test-2026-01-30",
  "status": "success",
  "generation_time_seconds": 9.8,
  "core": {
    "count": 1,
    "total_area_m2": 40.0
  },
  "corridors": {
    "pattern": "grid",
    "segment_count": 3,
    "total_area_m2": 286.3,
    "area_ratio": 9.5
  },
  "units": [
    {
      "id": "unit_1",
      "type": "1BR",
      "area_m2": 55.2,
      "polygon": {...},
      "centroid": [31.5, 24.0]
    }
  ],
  "metrics": {
    "boundary_area_m2": 3024.0,
    "total_used_m2": 2010.5,
    "total_wasted_m2": 1013.5,
    "coverage_percent": 66.5,
    "efficiency": 0.665,
    "units_count": 38
  }
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

**Backup Archive**: https://www.genspark.ai/api/files/s/n93vZ1pl (87MB)

---

**Built with ❤️ using Python, Shapely, FastAPI, and Cloudflare Pages**
