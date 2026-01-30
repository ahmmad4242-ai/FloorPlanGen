# FloorPlanGen API Documentation V2.5.1

## 📋 Overview

FloorPlanGen provides a REST API for generating architectural floor plans with intelligent corridor networks, multi-core support, and optimized unit placement.

**Base URL**: `http://localhost:8001` (development)  
**Version**: V2.5.1  
**Date**: 2026-01-30

---

## 🎯 Key Features (V2.5.1)

1. **Manual Corridor Pattern Selection** (`corridor_pattern`)
   - Grid (2×2, 3×3)
   - H-Pattern, U-Pattern, L-Pattern
   - Plus (+), T-Pattern, Line
   - Auto (intelligent selection)

2. **Multi-Core Support** (`core_count`)
   - 1 Core: Central placement (default)
   - 2 Cores: Dual placement for elongated buildings
   - 4 Cores: Quad placement for large buildings

3. **Professional Unit Placement**
   - Multi-pass algorithm (4 passes)
   - Corridor-connected units
   - Perimeter-facing for natural light
   - Mixed unit types (Studio, 1BR, 2BR, 3BR)

---

## 📡 API Endpoints

### 1. Generate Floor Plan

**Endpoint**: `POST /generate`

**Description**: Generate one or more floor plan variants based on provided constraints.

#### Request Body

```json
{
  "project_id": "string (required)",
  "dxf_url": "string (optional)",
  "dxf_file_path": "string (optional)",
  "boundary_layer": "string (default: BOUNDARY)",
  "variant_count": "integer (default: 5)",
  "constraints": {
    "architectural_constraints": {
      "core": {
        "core_count": 1,           // 🆕 V2.5.1: Multi-core support (1, 2, or 4)
        "elevators": 2,
        "stairs": 2,
        "net_area_m2": {
          "min": 30,
          "target": 40,
          "max": 50
        }
      },
      "circulation": {
        "corridor_pattern": "grid",  // 🆕 V2.5.1: Manual pattern selection
        "corridor_width_m": {
          "min": 2.0,
          "target": 2.2,
          "max": 2.5
        },
        "corridor_area_ratio": {
          "min": 0.08,
          "target": 0.10,
          "max": 0.15
        }
      },
      "units": [
        {
          "type": "Studio",
          "percentage": 20,
          "net_area_m2": {
            "min": 25,
            "target": 30,
            "max": 35
          }
        },
        {
          "type": "1BR",
          "percentage": 40,
          "net_area_m2": {
            "min": 45,
            "target": 55,
            "max": 65
          }
        },
        {
          "type": "2BR",
          "percentage": 30,
          "net_area_m2": {
            "min": 65,
            "target": 75,
            "max": 85
          }
        },
        {
          "type": "3BR",
          "percentage": 10,
          "net_area_m2": {
            "min": 85,
            "target": 100,
            "max": 115
          }
        }
      ]
    }
  }
}
```

#### Corridor Pattern Options

| Pattern | Description | Best For | Corridor Ratio |
|---------|-------------|----------|----------------|
| **grid** | 2×2 or 3×3 intersecting corridors | Large rectangular buildings | 12-16% |
| **H** | Double-loaded with cross corridor | Medium-large buildings | 9-11% |
| **U** | 3-sided perimeter corridor | Courtyard buildings | 10-12% |
| **L** | Two perpendicular corridors | L-shaped buildings | 8-10% |
| **+** (plus) | 4-directional from center | Square buildings | 9-11% |
| **T** | Main spine + branch | Medium buildings | 8-10% |
| **line** | Single straight corridor | Narrow buildings | 6-8% |
| **auto** | Intelligent selection based on shape | Any (default) | Varies |

#### Core Count Options

| Core Count | Placement | Best For | Building Size |
|------------|-----------|----------|---------------|
| **1** (default) | Central | Small-medium buildings | < 2000 m² |
| **2** | Both ends | Elongated buildings | 2000-4000 m² |
| **4** | Four corners | Very large buildings | > 4000 m² |

#### Response

```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "message": "Generated 5 variants successfully",
  "variants": [
    {
      "variant_id": "uuid-string",
      "variant_number": 1,
      "metrics": {
        "total_area": 3024.0,
        "usable_area": 2984.0,
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
      "dxf_download_url": "/variant/{variant_id}/download",
      "svg_preview_url": "/variant/{variant_id}/preview"
    }
  ]
}
```

---

## 🔧 Usage Examples

### Example 1: Grid Pattern with Single Core

```bash
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "test-grid-001",
    "boundary_layer": "BOUNDARY",
    "variant_count": 3,
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
          {"type": "1BR", "percentage": 60, "net_area_m2": {"min": 45, "target": 55, "max": 65}},
          {"type": "2BR", "percentage": 40, "net_area_m2": {"min": 65, "target": 75, "max": 85}}
        ]
      }
    }
  }'
```

### Example 2: H-Pattern with Quad Cores

```bash
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "test-h-pattern-001",
    "variant_count": 5,
    "constraints": {
      "architectural_constraints": {
        "core": {
          "core_count": 4,
          "elevators": 3,
          "stairs": 2,
          "net_area_m2": {"min": 35, "target": 45, "max": 55}
        },
        "circulation": {
          "corridor_pattern": "H",
          "corridor_width_m": {"min": 2.0, "target": 2.2, "max": 2.5}
        },
        "units": [
          {"type": "Studio", "percentage": 20, "net_area_m2": {"min": 25, "target": 30, "max": 35}},
          {"type": "1BR", "percentage": 40, "net_area_m2": {"min": 45, "target": 55, "max": 65}},
          {"type": "2BR", "percentage": 30, "net_area_m2": {"min": 65, "target": 75, "max": 85}},
          {"type": "3BR", "percentage": 10, "net_area_m2": {"min": 85, "target": 100, "max": 115}}
        ]
      }
    }
  }'
```

### Example 3: Auto Pattern with Dual Cores

```bash
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "test-auto-001",
    "variant_count": 3,
    "constraints": {
      "architectural_constraints": {
        "core": {
          "core_count": 2,
          "elevators": 2,
          "stairs": 2
        },
        "circulation": {
          "corridor_pattern": "auto"
        },
        "units": [
          {"type": "1BR", "percentage": 50, "net_area_m2": {"min": 45, "target": 55, "max": 65}},
          {"type": "2BR", "percentage": 50, "net_area_m2": {"min": 65, "target": 75, "max": 85}}
        ]
      }
    }
  }'
```

---

## 📊 Performance Metrics

### Typical Generation Times

| Boundary Size | Units | Cores | Pattern | Time |
|---------------|-------|-------|---------|------|
| 1500 m² | 20-25 | 1 | auto | 5-8s |
| 3000 m² | 35-40 | 1 | grid | 8-12s |
| 3000 m² | 35-40 | 2 | H | 9-13s |
| 5000 m² | 50-60 | 4 | grid | 12-18s |

### Coverage Statistics (V2.5.1)

```
Average Coverage:    66-77%
Average Efficiency:  55-65%
Corridor Ratio:      8-12% (grid: 12-16%)
Units per 1000m²:    11-13 units
Generation Success:  95%+
```

---

## 🐛 Common Issues & Solutions

### Issue 1: Low Coverage (<60%)

**Problem**: Units not filling available space

**Solutions**:
- Use `auto` or `H` pattern instead of `grid`
- Reduce `core_count` to 1
- Simplify boundary polygon (fewer vertices)
- Increase `corridor_area_ratio.max` to 0.18

### Issue 2: Too Many Corridors (>15%)

**Problem**: Grid pattern uses excessive corridor space

**Solutions**:
- Use `H`, `U`, or `+` pattern
- Set `corridor_pattern: "auto"` for intelligent selection
- Reduce `corridor_width_m.target` to 2.0

### Issue 3: Generation Timeout

**Problem**: Process takes >30 seconds

**Solutions**:
- Reduce `variant_count` to 3-5
- Simplify DXF input (remove details)
- Use simpler patterns (`line` or `T`)

---

## 🔒 Validation Rules

### Architectural Constraints

1. **Core Area**: 1-3% of total area
2. **Corridor Ratio**: 8-15% of total area
3. **Unit Areas**: Must meet min/max bounds
4. **Corridor Width**: 2.0-2.5m (architectural standard)
5. **Unit Distribution**: Sum of percentages = 100%

### Compliance Scoring

```
Score = (
  unit_count_compliance * 0.3 +
  unit_area_compliance * 0.3 +
  corridor_compliance * 0.2 +
  efficiency_score * 0.2
)

Passing Score: ≥ 0.70 (70%)
```

---

## 📦 Download & Preview

### Download DXF File

```bash
GET /variant/{variant_id}/download
```

**Response**: DXF file (AutoCAD 2010 format)

### Preview SVG

```bash
GET /variant/{variant_id}/preview
```

**Response**: SVG preview image

---

## 🎯 Best Practices

### 1. Pattern Selection

- **Small buildings** (<2000 m²): Use `T` or `line`
- **Medium buildings** (2000-4000 m²): Use `H` or `U`
- **Large buildings** (>4000 m²): Use `grid` with quad cores
- **Elongated buildings**: Use `L` or dual cores
- **Square buildings**: Use `+` or `H`

### 2. Core Placement

- **Single core** (default): Buildings < 2000 m²
- **Dual cores**: Elongated buildings or 2000-4000 m²
- **Quad cores**: Very large buildings > 4000 m² or complex shapes

### 3. Unit Mix

- **Residential**: 20% Studio, 40% 1BR, 30% 2BR, 10% 3BR
- **Affordable**: 40% Studio, 40% 1BR, 20% 2BR
- **Luxury**: 30% 1BR, 40% 2BR, 30% 3BR

### 4. Optimization

- Start with `variant_count: 5` to get variety
- Use `corridor_pattern: "auto"` for first attempt
- Adjust `corridor_area_ratio` if coverage is low
- Increase `variant_count` to 10-20 for best results

---

## 📚 Additional Resources

- **GitHub Repository**: https://github.com/ahmmad4242-ai/FloorPlanGen
- **README**: Full project documentation
- **Backup Archive**: https://www.genspark.ai/api/files/s/KQ3BLZ1X

---

## 📝 Version History

### V2.5.1 (2026-01-30) - Current
- ✅ Manual corridor pattern selection
- ✅ Multi-core support (1, 2, 4)
- ✅ Grid pattern (2×2, 3×3)
- ✅ API integration complete
- ✅ Coverage: 66-77%

### V2.4.3 (2026-01-28)
- Baseline: Region-based placement
- Coverage: 66%

---

**Built with ❤️ using Python, FastAPI, Shapely, and ezdxf**
