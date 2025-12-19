#!/usr/bin/env python3
"""
Clear all data for the current user from Supabase
This will remove ALL player records and stats for a fresh start
"""

from supabase import create_client, Client

# Configuration
SUPABASE_URL = "https://kswwbqumgsdissnwuiab.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtzd3dicXVtZ3NkaXNzbnd1aWFiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ0ODMwNTIsImV4cCI6MjA4MDA1OTA1Mn0.b-z8JqL1dBYJcrrzSt7u6VAaFAtTOl1vqqtFFgHkJ50"
USER_ID = "116cc929-d60f-4ae4-ac53-b228b91ea8b3"

def clear_all_data():
    """Delete all records for the current user"""
    
    print("="*80)
    print("🗑️  CLEARING ALL DATA FOR USER")
    print("="*80)
    print(f"User ID: {USER_ID}")
    print("\n⚠️  WARNING: This will delete ALL player records and stats!")
    
    confirm = input("\nType 'DELETE' to confirm: ")
    
    if confirm != "DELETE":
        print("\n❌ Cancelled. No data was deleted.")
        return
    
    print("\n🔄 Deleting all records...")
    
    # Initialize Supabase client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Get count before deletion
        before = supabase.table('aads_players').select('id', count='exact').eq('user_id', USER_ID).execute()
        count_before = before.count if hasattr(before, 'count') else len(before.data)
        
        print(f"\nFound {count_before} records to delete")
        
        # Delete all records for this user
        result = supabase.table('aads_players').delete().eq('user_id', USER_ID).execute()
        
        print(f"\n✅ SUCCESS! Deleted {count_before} records")
        print("\n📊 Your account is now clean:")
        print("   • No matches")
        print("   • No players")
        print("   • No stats")
        print("\n🚀 Ready for fresh data import!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    clear_all_data()
