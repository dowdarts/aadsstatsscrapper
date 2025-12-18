import json

with open('event_props.json') as f:
    data = json.load(f)

# Check tournament info
tournament_info = data.get('tournamentInfo', {})
events = tournament_info.get('events', [])

print(f"Events in tournament: {len(events)}")

for event in events:
    print(f"\nEvent: {event.get('event_label', 'Unknown')}")
    print(f"  Type: {event.get('event_type', 'Unknown')}")
    print(f"  Match count: {event.get('match_count', 0)}")
    
    # Check if there are matches embedded
    if 'matches' in event:
        matches = event['matches']
        print(f"  Embedded matches: {len(matches)}")
        if matches:
            sample = matches[0]
            print(f"  Sample match keys: {list(sample.keys())[:10]}")
            print(f"  Sample match ID: {sample.get('id', 'N/A')}")

# Check boards - they might have match info
boards = tournament_info.get('boards', [])
print(f"\n\nBoards: {len(boards)}")
if boards:
    sample_board = boards[0]
    print(f"Sample board keys: {list(sample_board.keys())}")
    if 'match' in sample_board or 'match_id' in sample_board:
        print(f"  Has match info!")
        print(json.dumps(sample_board, indent=2)[:500])
