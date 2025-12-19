-- ============================================================================
-- SUPABASE SCHEMA MIGRATION: Add Advanced Stats & Fix Unique Constraints
-- ============================================================================
-- 
-- Run this in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/kswwbqumgsdissnwuiab/sql
--
-- Purpose:
-- 1. Allow multiple match records per player
-- 2. Add advanced statistics columns (180s, 140+, 100+, checkout stats, etc.)
-- 3. Create proper unique constraint for match data
-- ============================================================================

-- STEP 1: Drop the unique constraint on player_name
-- This prevents "duplicate key" errors when same player has multiple matches
ALTER TABLE aads_players 
DROP CONSTRAINT IF EXISTS aads_players_name_key;

-- STEP 2: Add match_id and event_name columns (if not exists)
-- match_id: Stores the DartConnect match ID for each match record
-- event_name: Stores the event name (e.g., "Atlantic Amateur Dart Series Event #1")
ALTER TABLE aads_players 
ADD COLUMN IF NOT EXISTS match_id TEXT;

ALTER TABLE aads_players 
ADD COLUMN IF NOT EXISTS event_name TEXT;

-- STEP 3: Create composite unique index
-- Ensures one record per player per match, but allows same player in multiple matches
-- Note: Uses 'name' column (existing) not 'player_name'
DROP INDEX IF EXISTS aads_players_match_unique;
CREATE UNIQUE INDEX aads_players_match_unique 
ON aads_players (user_id, event_name, match_id, name);

-- ============================================================================
-- STEP 4: Add Advanced Statistics Columns
-- ============================================================================

-- First 9 darts average
ALTER TABLE aads_players 
ADD COLUMN IF NOT EXISTS first_nine_avg DECIMAL(5,2);

-- High score counts
ALTER TABLE aads_players 
ADD COLUMN IF NOT EXISTS count_180s INTEGER DEFAULT 0;

ALTER TABLE aads_players 
ADD COLUMN IF NOT EXISTS count_140_plus INTEGER DEFAULT 0;

ALTER TABLE aads_players 
ADD COLUMN IF NOT EXISTS count_100_plus INTEGER DEFAULT 0;

ALTER TABLE aads_players 
ADD COLUMN IF NOT EXISTS highest_score INTEGER;

-- Checkout statistics
ALTER TABLE aads_players 
ADD COLUMN IF NOT EXISTS checkout_efficiency TEXT;

ALTER TABLE aads_players 
ADD COLUMN IF NOT EXISTS checkout_opportunities INTEGER DEFAULT 0;

ALTER TABLE aads_players 
ADD COLUMN IF NOT EXISTS checkouts_hit INTEGER DEFAULT 0;

ALTER TABLE aads_players 
ADD COLUMN IF NOT EXISTS highest_checkout INTEGER;

ALTER TABLE aads_players 
ADD COLUMN IF NOT EXISTS avg_finish DECIMAL(5,2);

-- DartConnect leaderboard link
ALTER TABLE aads_players 
ADD COLUMN IF NOT EXISTS card_link TEXT;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Check table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'aads_players' 
ORDER BY ordinal_position;

-- Check indexes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'aads_players';

-- ============================================================================
-- SUCCESS! 
-- ============================================================================
-- After running this:
-- ✅ Players can have multiple match records
-- ✅ All advanced stats columns added
-- ✅ Proper unique constraint in place
-- ✅ Ready to run: python batch_scrape_comprehensive.py
-- ============================================================================
