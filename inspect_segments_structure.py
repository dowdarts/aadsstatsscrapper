"""
Deep inspection of segments structure to find turn-by-turn data
"""

import json

# Load the previously saved props
with open('event_props.json', 'r') as f:
    page_data = json.load(f)

props = page_data.get('props', {})
segments = props.get('segments', {})

print("=" * 80)
print("SEGMENTS STRUCTURE ANALYSIS")
print("=" * 80)

for game_key, game_data in segments.items():
    print(f"\nGame: '{game_key}'")
    print(f"  Type: {type(game_data)}")
    print(f"  Length: {len(game_data) if isinstance(game_data, list) else 'N/A'}")
    
    if isinstance(game_data, list):
        for leg_index, leg_data in enumerate(game_data, 1):
            print(f"\n  Leg {leg_index}:")
            print(f"    Type: {type(leg_data)}")
            
            if isinstance(leg_data, dict):
                print(f"    Keys ({len(leg_data.keys())}): {list(leg_data.keys())}")
                
                # Show first few items of each key
                for key, value in leg_data.items():
                    if isinstance(value, list):
                        print(f"\n    '{key}': list with {len(value)} items")
                        if value:
                            print(f"      First item: {value[0]}")
                            if len(value) > 1:
                                print(f"      Second item: {value[1]}")
                    elif isinstance(value, dict):
                        print(f"\n    '{key}': dict with keys: {list(value.keys())}")
                    else:
                        print(f"    '{key}': {value}")
                
                # Only show first leg in detail
                if leg_index == 1:
                    print(f"\n    FULL LEG 1 DATA:")
                    print(json.dumps(leg_data, indent=6))
            
            # Only analyze first 2 legs
            if leg_index >= 2:
                break
