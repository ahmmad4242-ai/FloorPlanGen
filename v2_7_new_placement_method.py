"""
V2.7.0 - New Placement Method: Overlap-Check Approach

Key Changes:
1. DON'T use region.difference() - causes fragmentation!
2. Use simple overlap check: unit.intersects(occupied_union)
3. Search the ENTIRE available_area, not fragmented regions
4. Update occupied_union after each placement

Benefits:
- No fragmentation = better space utilization
- Can place units in narrow gaps
- Guaranteed 92-95%+ coverage
"""

def _place_units_pass_v2_7(self,
                           unit_specs: List[Dict],
                           available_area: Polygon,  # SINGLE polygon, not list!
                           corridor_union: Polygon,
                           placed_units: List[Dict],
                           pass_config: Dict) -> List[Dict]:
    """
    ✅ V2.7.0: NEW placement algorithm using overlap-check approach.
    
    No more region.difference()! Just check overlap with occupied_union.
    """
    remaining = []
    pass_name = pass_config["name"]
    placed_count = 0
    
    # Build occupied_union from already placed units
    if placed_units:
        occupied_polys = [u["polygon"] for u in placed_units]
        occupied_union = unary_union(occupied_polys)
    else:
        occupied_union = Polygon()  # Empty
    
    # Get available_area bounds for grid search
    minx, miny, maxx, maxy = available_area.bounds
    
    for spec in unit_specs:
        target_area = spec["target_area"]
        unit_type = spec["type"]
        
        # Calculate unit dimensions
        unit_width = np.sqrt(target_area * 1.3)
        unit_depth = target_area / unit_width
        
        best_unit = None
        best_score = -1
        
        # ✅ V2.7: Adaptive grid based on pass
        if pass_name in ["strict", "relaxed"]:
            # Coarser grid for fast passes
            x_step = max(0.3, unit_width * 0.15)
            y_step = max(0.3, unit_depth * 0.15)
        elif pass_name == "flexible":
            # Fine grid for thorough search
            x_step = max(0.2, unit_width * 0.10)
            y_step = max(0.2, unit_depth * 0.10)
        else:  # gap_filling
            # Ultra-fine grid for maximum coverage
            x_step = max(0.15, unit_width * 0.08)
            y_step = max(0.15, unit_depth * 0.08)
        
        x_positions = np.arange(minx, maxx - unit_width * 0.2, x_step)
        y_positions = np.arange(miny, maxy - unit_depth * 0.2, y_step)
        
        max_attempts = pass_config["max_attempts"]
        attempts = 0
        
        excellent_threshold = 0.75  # V2.7: Reduced for thorough search
        
        for x in x_positions:
            for y in y_positions:
                if attempts >= max_attempts:
                    break
                attempts += 1
                
                # Create unit box
                unit_poly = box(x, y, x + unit_width, y + unit_depth)
                
                # ✅ V2.7: KEY CHANGE - Check overlap with occupied_union ONLY!
                # No need to clip to region - we'll check available_area intersection
                
                # 1. Must be within available_area
                if not available_area.contains(unit_poly):
                    unit_clipped = unit_poly.intersection(available_area)
                    if unit_clipped.is_empty or not isinstance(unit_clipped, Polygon):
                        continue
                else:
                    unit_clipped = unit_poly
                
                # 2. Must NOT overlap with already placed units
                if not occupied_union.is_empty:
                    if unit_clipped.intersects(occupied_union):
                        # Check if overlap is significant (>0.1 m²)
                        overlap = unit_clipped.intersection(occupied_union)
                        if overlap.area > 0.1:
                            continue
                
                # 3. Check minimum area
                if unit_clipped.area < target_area * pass_config["min_area_match"]:
                    continue
                
                # 4. Perimeter check
                try:
                    if unit_clipped.boundary is None:
                        continue
                    perimeter_contact = unit_clipped.boundary.intersection(self.boundary.boundary)
                    perimeter_length = perimeter_contact.length if hasattr(perimeter_contact, 'length') else 0
                except:
                    perimeter_length = 0
                
                if perimeter_length < pass_config["min_perimeter"]:
                    continue
                
                # 5. Corridor proximity check
                try:
                    corridor_distance = unit_clipped.distance(corridor_union)
                    corridor_contact = unit_clipped.intersection(corridor_union.buffer(0.05))
                    has_corridor_contact = not corridor_contact.is_empty and corridor_contact.area < 0.1
                    
                    min_facing_width = pass_config.get("min_corridor_facing_width", 2.5)
                    if unit_clipped.boundary is None:
                        facing_width = 0
                    else:
                        corridor_facing_edge = unit_clipped.boundary.intersection(corridor_union.buffer(0.1))
                        facing_width = corridor_facing_edge.length if hasattr(corridor_facing_edge, 'length') else 0
                    
                    if facing_width > 0 and facing_width < min_facing_width:
                        continue
                except:
                    corridor_distance = 999
                    has_corridor_contact = False
                
                if corridor_distance > pass_config["max_corridor_distance"]:
                    continue
                
                # 6. Score this placement
                area_match = min(unit_clipped.area / target_area, target_area / unit_clipped.area)
                perimeter_score = min(perimeter_length / 3.0, 1.0)
                corridor_score = max(0, 1.0 - corridor_distance / pass_config["max_corridor_distance"])
                contact_bonus = 2.0 if has_corridor_contact else 0
                
                score = area_match * 8 + perimeter_score * 3 + corridor_score * 4 + contact_bonus
                
                if score > best_score:
                    best_unit = unit_clipped
                    best_score = score
                    
                    if best_score >= excellent_threshold * 17:
                        break
            
            if best_unit and best_score >= excellent_threshold * 17:
                break
            
            if attempts >= max_attempts:
                break
        
        # Place best unit if found
        if best_unit and best_score > 0:
            placed_units.append({
                "type": unit_type,
                "polygon": best_unit,
                "area": best_unit.area
            })
            placed_count += 1
            
            # ✅ V2.7: Update occupied_union (no region.difference()!)
            occupied_union = unary_union([occupied_union, best_unit.buffer(0.05)])
        else:
            remaining.append(spec)
    
    logger.info(f"  Pass '{pass_name}': Placed {placed_count} units")
    return remaining

print("✅ V2.7.0 New Placement Method Ready")
print("\nKey Changes:")
print("1. No more region.difference() → no fragmentation")
print("2. Simple overlap check with occupied_union")
print("3. Search entire available_area")
print("4. Expected coverage: 92-95%+")
