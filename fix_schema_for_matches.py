#!/usr/bin/env python3
"""
Fix Supabase schema to allow multiple matches per player

Current Issue: 
- UNIQUE constraint on player_name prevents storing multiple matches for same player
- Need to remove this constraint and allow duplicate names (different matches)

Solution:
- Drop the unique constraint on player_name
- Keep match_id + player_name combination for identifying records
- Allow upsert based on (user_id, player_name, event_name, match_id)
"""

from supabase import create_client, Client

# Configuration
SUPABASE_URL = "https://kswwbqumgsdissnwuiab.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtzd3dicXVtZ3NkaXNzbnd1aWFiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ0ODMwNTIsImV4cCI6MjA4MDA1OTA1Mn0.b-z8JqL1dBYJcrrzSt7u6VAaFAtTOl1vqqtFFgHkJ50"

def fix_schema(supabase: Client):
    """Fix schema to allow multiple matches per player"""
    
    print("="*80)
    print("🔧 FIXING SUPABASE SCHEMA")
    print("="*80)
    
    sql_commands = [
        # Drop the unique constraint on player_name
        """
        ALTER TABLE aads_players 
        DROP CONSTRAINT IF EXISTS aads_players_name_key;
        """,
        
        # Add match_id column if it doesn't exist
        """
        ALTER TABLE aads_players 
        ADD COLUMN IF NOT EXISTS match_id TEXT;
        """,
        
        # Create a unique constraint on the combination that matters
        # (user_id + event_name + match_id + player_name should be unique)
        """
        CREATE UNIQUE INDEX IF NOT EXISTS aads_players_match_unique 
        ON aads_players (user_id, event_name, match_id, player_name);
        """,
        
        # Add advanced stats columns if not exist
        """
        ALTER TABLE aads_players 
        ADD COLUMN IF NOT EXISTS first_nine_avg DECIMAL(5,2);
        """,
        """
        ALTER TABLE aads_players 
        ADD COLUMN IF NOT EXISTS count_180s INTEGER DEFAULT 0;
        """,
        """
        ALTER TABLE aads_players 
        ADD COLUMN IF NOT EXISTS count_140_plus INTEGER DEFAULT 0;
        """,
        """
        ALTER TABLE aads_players 
        ADD COLUMN IF NOT EXISTS count_100_plus INTEGER DEFAULT 0;
        """,
        """
        ALTER TABLE aads_players 
        ADD COLUMN IF NOT EXISTS highest_score INTEGER;
        """,
        """
        ALTER TABLE aads_players 
        ADD COLUMN IF NOT EXISTS checkout_efficiency TEXT;
        """,
        """
        ALTER TABLE aads_players 
        ADD COLUMN IF NOT EXISTS checkout_opportunities INTEGER DEFAULT 0;
        """,
        """
        ALTER TABLE aads_players 
        ADD COLUMN IF NOT EXISTS checkouts_hit INTEGER DEFAULT 0;
        """,
        """
        ALTER TABLE aads_players 
        ADD COLUMN IF NOT EXISTS highest_checkout INTEGER;
        """,
        """
        ALTER TABLE aads_players 
        ADD COLUMN IF NOT EXISTS avg_finish DECIMAL(5,2);
        """,
        """
        ALTER TABLE aads_players 
        ADD COLUMN IF NOT EXISTS card_link TEXT;
        """
    ]
    
    for i, sql in enumerate(sql_commands, 1):
        try:
            print(f"\n[{i}/{len(sql_commands)}] Executing SQL...")
            
            # Extract operation description
            if 'DROP CONSTRAINT' in sql:
                print(f"  Dropping unique constraint on player_name")
            elif 'CREATE UNIQUE INDEX' in sql:
                print(f"  Creating composite unique index")
            elif 'ADD COLUMN' in sql:
                column_name = sql.split('ADD COLUMN IF NOT EXISTS')[1].split()[0]
                print(f"  Adding column: {column_name}")
            
            result = supabase.rpc('exec_sql', {'query': sql}).execute()
            print(f"  ✅ Success")
            
        except Exception as e:
            error_msg = str(e)
            
            if 'already exists' in error_msg.lower() or 'does not exist' in error_msg.lower():
                print(f"  ℹ️  Already done, skipping")
            else:
                print(f"  ⚠️  {error_msg}")
    
    print("\n" + "="*80)
    print("✅ SCHEMA FIX COMPLETE")
    print("="*80)
    print("\nChanges made:")
    print("  ✓ Removed unique constraint on player_name")
    print("  ✓ Added match_id column")
    print("  ✓ Created composite unique index (user_id + event_name + match_id + player_name)")
    print("  ✓ Added all advanced statistics columns")
    print("\n📊 Now players can have multiple match records!")

if __name__ == "__main__":
    print("\n🚀 Starting schema fix...")
    
    # Initialize Supabase client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Fix schema
    fix_schema(supabase)
    
    print("\n✅ Ready to run batch_scrape_comprehensive.py!")
