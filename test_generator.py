"""
Test Python Generator with real generation
"""
import sys
import json
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.main import generate_single_variant, create_sample_dxf
from shapely.geometry import box

def test_generator():
    print("🧪 Testing Python Generator Engine...\n")
    
    # Create sample DXF
    print("1️⃣ Creating sample DXF...")
    dxf_path = create_sample_dxf("test-project")
    print(f"   ✓ Created: {dxf_path}\n")
    
    # Prepare test data
    print("2️⃣ Preparing test constraints...")
    boundary = box(0, 0, 30, 20)  # 30m x 20m floor
    obstacles = []
    fixed_elements = {"core": [], "stairs": [], "elevators": [], "shafts": []}
    
    constraints = {
        "units": [
            {"type": "1BR", "count": 6, "net_area_m2": {"min": 55, "max": 70}},
            {"type": "2BR", "count": 4, "net_area_m2": {"min": 85, "max": 105}}
        ],
        "circulation": {
            "corridor_width_m": {"min": 2.0, "target": 2.2},
            "corridor_area_ratio": {"max": 0.18}
        },
        "core": {
            "elevators": 2,
            "stairs": 2,
            "preferred_zones": ["center"]
        },
        "service": {
            "service_rooms_ratio": {"min": 0.05, "max": 0.08},
            "must_include": ["ELECTRICAL", "MECH"]
        }
    }
    print(f"   ✓ Constraints prepared: {len(constraints['units'])} unit types\n")
    
    # Generate variant
    print("3️⃣ Generating floor plan variant...")
    try:
        variant = generate_single_variant(
            project_id="test-project",
            variant_number=1,
            boundary=boundary,
            obstacles=obstacles,
            fixed_elements=fixed_elements,
            constraints=constraints
        )
        
        print("   ✓ Generation successful!\n")
        
        # Display results
        print("📊 Generated Variant Details:")
        print(f"   • Variant ID: {variant['variant_id']}")
        print(f"   • Score: {variant['score']:.2f}/100")
        print(f"   • DXF File: {variant['dxf_file_path']}")
        
        metadata = variant['metadata']
        print(f"\n   Metrics:")
        print(f"   • Total Area: {metadata['total_area']:.2f} m²")
        print(f"   • Usable Area: {metadata['usable_area']:.2f} m²")
        print(f"   • Core Area: {metadata['core_area']:.2f} m²")
        print(f"   • Corridor Area: {metadata['corridor_area']:.2f} m²")
        print(f"   • Units Area: {metadata['units_area']:.2f} m²")
        print(f"   • Efficiency: {metadata['efficiency']:.1%}")
        print(f"   • Corridor Ratio: {metadata['corridor_ratio']:.1%}")
        print(f"   • Units Count: {metadata['units_count']}")
        
        units_by_type = metadata['units_by_type']
        print(f"\n   Units by Type:")
        for unit_type, count in units_by_type.items():
            print(f"   • {unit_type}: {count} units")
        
        compliance = variant['compliance']
        print(f"\n   Compliance:")
        print(f"   • Overall Passed: {'✓' if compliance['overall_passed'] else '✗'}")
        print(f"   • Score: {compliance['score']:.2f}/100")
        
        print("\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"   ✗ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_generator()
    sys.exit(0 if success else 1)
