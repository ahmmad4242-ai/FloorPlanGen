#!/usr/bin/env python3
"""Test current pass configuration"""

# Current configuration
passes = {
    "Pass 1 (Strict)": {
        "min_perimeter": 0.8,
        "max_corridor_distance": 0.3,  # 30cm - VERY strict!
        "min_corridor_facing_width": 2.5,
        "min_area_match": 0.60,
        "max_attempts": 300
    },
    "Pass 2 (Relaxed)": {
        "min_perimeter": 0.3,
        "max_corridor_distance": 1.0,  # 1m - STILL TOO STRICT!
        "min_corridor_facing_width": 2.0,
        "min_area_match": 0.50,
        "max_attempts": 200
    },
    "Pass 3 (Flexible)": {
        "min_perimeter": 0.0,
        "max_corridor_distance": 2.5,  # 2.5m - TOO STRICT for fallback!
        "min_corridor_facing_width": 1.5,
        "min_area_match": 0.40
    }
}

print("=" * 80)
print("🔍 CURRENT PASS CONFIGURATION ANALYSIS")
print("=" * 80)

for pass_name, config in passes.items():
    print(f"\n{pass_name}:")
    for key, value in config.items():
        print(f"  {key}: {value}")
        
print("\n" + "=" * 80)
print("❌ IDENTIFIED PROBLEMS:")
print("=" * 80)

problems = [
    "1. Pass 2: max_corridor_distance = 1.0m is TOO STRICT!",
    "   → Most units are >1m from corridor after Pass 1",
    "   → Should be 3.0-5.0m for 'Relaxed' pass",
    "",
    "2. Pass 3: max_corridor_distance = 2.5m is STILL TOO STRICT!",
    "   → This is supposed to be the FALLBACK pass",
    "   → Should be 10.0-15.0m or UNLIMITED",
    "",
    "3. Pass 2: min_corridor_facing_width = 2.0m is too strict",
    "   → Should allow 1.0m or even 0m for relaxed placement",
    "",
    "4. All passes: max_attempts too low after V2.4.2 optimization",
    "   → Pass 1: 300 OK",
    "   → Pass 2: 200 → should be 500",
    "   → Pass 3: 200 → should be 800"
]

for problem in problems:
    print(problem)

print("\n" + "=" * 80)
print("✅ RECOMMENDED FIX:")
print("=" * 80)

recommended = {
    "Pass 1 (Strict)": {
        "min_perimeter": 0.8,
        "max_corridor_distance": 0.5,  # Slightly relaxed: 30cm → 50cm
        "min_corridor_facing_width": 2.5,
        "min_area_match": 0.60,
        "max_attempts": 300
    },
    "Pass 2 (Relaxed)": {
        "min_perimeter": 0.0,  # Remove perimeter requirement
        "max_corridor_distance": 5.0,  # Relaxed: 1m → 5m
        "min_corridor_facing_width": 1.0,  # Relaxed: 2m → 1m
        "min_area_match": 0.50,
        "max_attempts": 500  # Increased
    },
    "Pass 3 (Flexible)": {
        "min_perimeter": 0.0,
        "max_corridor_distance": 15.0,  # Very relaxed: 2.5m → 15m
        "min_corridor_facing_width": 0.0,  # No requirement
        "min_area_match": 0.40,
        "max_attempts": 800  # Increased significantly
    }
}

for pass_name, config in recommended.items():
    print(f"\n{pass_name}:")
    for key, value in config.items():
        print(f"  {key}: {value}")

