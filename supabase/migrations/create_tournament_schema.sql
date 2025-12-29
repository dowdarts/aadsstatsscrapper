-- AADS Tournament Management System - Complete Database Schema
-- Created: 2025-12-29
-- Description: Comprehensive schema for manual tournament stats input and tracking

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- PLAYERS TABLE
-- Stores player profile information including photos as base64
-- ============================================================================
CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    nickname TEXT,
    age INTEGER,
    hometown TEXT,
    photo_base64 TEXT, -- Base64 encoded player photo
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_players_name ON players(name);

-- ============================================================================
-- PLAYER DART SETUP TABLE
-- Stores equipment details for each player
-- ============================================================================
CREATE TABLE player_dart_setup (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    barrel TEXT,
    shaft TEXT,
    flight TEXT,
    weight TEXT,
    details TEXT, -- Additional equipment notes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_player_dart_setup_player_id ON player_dart_setup(player_id);

-- ============================================================================
-- SERIES TABLE
-- Represents a season/series of events
-- ============================================================================
CREATE TABLE series (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    year INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_series_year ON series(year);

-- ============================================================================
-- EVENTS TABLE
-- Individual tournaments within a series (7 events per series)
-- ============================================================================
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    series_id UUID NOT NULL REFERENCES series(id) ON DELETE CASCADE,
    event_number INTEGER NOT NULL, -- 1-7
    event_date DATE,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published')),
    version_number INTEGER DEFAULT 0, -- Increments on publish for auto-refresh
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_events_series_id ON events(series_id);
CREATE INDEX idx_events_status ON events(status);
CREATE UNIQUE INDEX idx_events_series_event_number ON events(series_id, event_number);

-- ============================================================================
-- MATCHES TABLE
-- Individual matches within events (round-robin, QF, SF, Final)
-- ============================================================================
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    round_type TEXT NOT NULL, -- 'round_robin', 'qf', 'sf', 'final'
    round_number INTEGER, -- For round-robin: 1-5
    group_name TEXT, -- 'A' or 'B' for round-robin, NULL for knockouts
    player1_id UUID NOT NULL REFERENCES players(id),
    player2_id UUID NOT NULL REFERENCES players(id),
    player1_sets INTEGER DEFAULT 0,
    player2_sets INTEGER DEFAULT 0,
    player1_legs INTEGER DEFAULT 0,
    player2_legs INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_matches_event_id ON matches(event_id);
CREATE INDEX idx_matches_player1_id ON matches(player1_id);
CREATE INDEX idx_matches_player2_id ON matches(player2_id);
CREATE INDEX idx_matches_round_type ON matches(round_type);

-- ============================================================================
-- MATCH STATS TABLE
-- Detailed statistics for each player in each match
-- ============================================================================
CREATE TABLE match_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES players(id),
    legs_won INTEGER NOT NULL DEFAULT 0,
    legs_lost INTEGER NOT NULL DEFAULT 0,
    three_dart_avg DECIMAL(5,2), -- e.g., 85.47
    count_100plus INTEGER DEFAULT 0,
    count_120plus INTEGER DEFAULT 0,
    count_140plus INTEGER DEFAULT 0,
    count_160plus INTEGER DEFAULT 0,
    count_180s INTEGER DEFAULT 0,
    checkouts_hit INTEGER DEFAULT 0,
    checkouts_opportunities INTEGER DEFAULT 0,
    checkout_percentage DECIMAL(5,2), -- Calculated: (hit/opportunities)*100
    highest_finish INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_match_stats_match_id ON match_stats(match_id);
CREATE INDEX idx_match_stats_player_id ON match_stats(player_id);
CREATE UNIQUE INDEX idx_match_stats_match_player ON match_stats(match_id, player_id);

-- ============================================================================
-- PLAYER PERSONAL BESTS TABLE
-- Tracks each player's best placement across all events
-- ============================================================================
CREATE TABLE player_personal_bests (
    player_id UUID PRIMARY KEY REFERENCES players(id) ON DELETE CASCADE,
    best_placement INTEGER, -- 1=Champion, 2=Finalist, 3=SF, 4=QF, 5-10=Group
    best_event_id UUID REFERENCES events(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_player_personal_bests_event_id ON player_personal_bests(best_event_id);

-- ============================================================================
-- EDIT HISTORY TABLE
-- Audit log tracking all changes to events
-- ============================================================================
CREATE TABLE edit_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    changes_json JSONB, -- Stores field changes: {field: {old: X, new: Y}}
    admin_note TEXT
);

CREATE INDEX idx_edit_history_event_id ON edit_history(event_id);
CREATE INDEX idx_edit_history_timestamp ON edit_history(timestamp DESC);

-- ============================================================================
-- APP VERSION TABLE
-- Single-row table for tracking published version for auto-refresh polling
-- ============================================================================
CREATE TABLE app_version (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1), -- Ensure only one row
    version_number INTEGER NOT NULL DEFAULT 0,
    last_published_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert initial version row
INSERT INTO app_version (id, version_number, last_published_at) 
VALUES (1, 0, NOW());

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Enable public read-only access for display app
-- Admin writes handled via service_role key in backend
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE players ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_dart_setup ENABLE ROW LEVEL SECURITY;
ALTER TABLE series ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE match_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_personal_bests ENABLE ROW LEVEL SECURITY;
ALTER TABLE edit_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_version ENABLE ROW LEVEL SECURITY;

-- Public read-only policies (for anon key used by display app)
CREATE POLICY "Public can read players" ON players FOR SELECT USING (true);
CREATE POLICY "Public can read player_dart_setup" ON player_dart_setup FOR SELECT USING (true);
CREATE POLICY "Public can read series" ON series FOR SELECT USING (true);
CREATE POLICY "Public can read published events" ON events FOR SELECT USING (status = 'published');
CREATE POLICY "Public can read matches from published events" ON matches FOR SELECT 
    USING (event_id IN (SELECT id FROM events WHERE status = 'published'));
CREATE POLICY "Public can read match_stats from published events" ON match_stats FOR SELECT 
    USING (match_id IN (SELECT m.id FROM matches m JOIN events e ON m.event_id = e.id WHERE e.status = 'published'));
CREATE POLICY "Public can read player_personal_bests" ON player_personal_bests FOR SELECT USING (true);
CREATE POLICY "Public can read edit_history" ON edit_history FOR SELECT USING (true);
CREATE POLICY "Public can read app_version" ON app_version FOR SELECT USING (true);

-- Note: INSERT/UPDATE/DELETE operations will be performed using service_role key
-- in the backend (database_manager.py), which bypasses RLS

-- ============================================================================
-- HELPER VIEWS
-- Pre-computed views for common queries
-- ============================================================================

-- View: Player Career Statistics (All Published Events)
CREATE OR REPLACE VIEW player_career_stats AS
SELECT 
    p.id AS player_id,
    p.name,
    p.nickname,
    COUNT(DISTINCT m.event_id) AS total_events,
    SUM(ms.legs_won) AS total_legs_won,
    SUM(ms.legs_won + ms.legs_lost) AS total_legs_played,
    CASE 
        WHEN SUM(ms.legs_won + ms.legs_lost) > 0 
        THEN ROUND((SUM(ms.legs_won)::DECIMAL / SUM(ms.legs_won + ms.legs_lost)) * 100, 2)
        ELSE 0 
    END AS legs_won_percentage,
    ROUND(AVG(ms.three_dart_avg), 2) AS career_avg,
    SUM(ms.count_180s) AS total_180s,
    SUM(ms.count_160plus) AS total_160plus,
    SUM(ms.count_140plus) AS total_140plus,
    SUM(ms.count_120plus) AS total_120plus,
    SUM(ms.count_100plus) AS total_100plus,
    SUM(ms.checkouts_hit) AS total_checkouts_hit,
    SUM(ms.checkouts_opportunities) AS total_checkouts_opportunities,
    CASE 
        WHEN SUM(ms.checkouts_opportunities) > 0 
        THEN ROUND((SUM(ms.checkouts_hit)::DECIMAL / SUM(ms.checkouts_opportunities)) * 100, 2)
        ELSE 0 
    END AS career_checkout_percentage,
    MAX(ms.highest_finish) AS career_highest_finish
FROM players p
LEFT JOIN match_stats ms ON p.id = ms.player_id
LEFT JOIN matches m ON ms.match_id = m.id
LEFT JOIN events e ON m.event_id = e.id
WHERE e.status = 'published'
GROUP BY p.id, p.name, p.nickname;

-- View: Event Leaderboard (for specific event)
CREATE OR REPLACE VIEW event_leaderboards AS
SELECT 
    e.id AS event_id,
    e.series_id,
    e.event_number,
    p.id AS player_id,
    p.name,
    p.nickname,
    SUM(ms.legs_won) AS legs_won,
    SUM(ms.legs_won + ms.legs_lost) AS legs_played,
    ROUND(AVG(ms.three_dart_avg), 2) AS event_avg,
    SUM(ms.count_180s) AS event_180s,
    SUM(ms.checkouts_hit) AS checkouts_hit,
    SUM(ms.checkouts_opportunities) AS checkouts_opportunities,
    CASE 
        WHEN SUM(ms.checkouts_opportunities) > 0 
        THEN ROUND((SUM(ms.checkouts_hit)::DECIMAL / SUM(ms.checkouts_opportunities)) * 100, 2)
        ELSE 0 
    END AS event_checkout_percentage
FROM events e
JOIN matches m ON e.id = m.event_id
JOIN match_stats ms ON m.id = ms.match_id
JOIN players p ON ms.player_id = p.id
WHERE e.status = 'published'
GROUP BY e.id, e.series_id, e.event_number, p.id, p.name, p.nickname;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function: Update player personal best automatically
CREATE OR REPLACE FUNCTION update_player_personal_best()
RETURNS TRIGGER AS $$
BEGIN
    -- This would be called after match results are inserted
    -- For now, personal bests will be updated manually in application logic
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function: Auto-update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for auto-updating timestamps
CREATE TRIGGER update_players_timestamp BEFORE UPDATE ON players
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_player_dart_setup_timestamp BEFORE UPDATE ON player_dart_setup
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_events_timestamp BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Additional indexes for common query patterns
CREATE INDEX idx_events_version_number ON events(version_number DESC);
CREATE INDEX idx_matches_event_round ON matches(event_id, round_type, round_number);
CREATE INDEX idx_match_stats_player_3da ON match_stats(player_id, three_dart_avg DESC);
CREATE INDEX idx_match_stats_180s ON match_stats(count_180s DESC);

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE players IS 'Player profiles with personal information and photos';
COMMENT ON TABLE player_dart_setup IS 'Equipment details for each player';
COMMENT ON TABLE series IS 'Tournament series (seasons)';
COMMENT ON TABLE events IS 'Individual events within a series (7 per series)';
COMMENT ON TABLE matches IS 'Individual matches within events';
COMMENT ON TABLE match_stats IS 'Detailed statistics for each player in each match';
COMMENT ON TABLE player_personal_bests IS 'Tracking best placement for each player';
COMMENT ON TABLE edit_history IS 'Audit log of all changes to events';
COMMENT ON TABLE app_version IS 'Version tracking for auto-refresh polling';

COMMENT ON COLUMN events.status IS 'draft: not visible on display app, published: visible to fans';
COMMENT ON COLUMN events.version_number IS 'Increments each publish to trigger auto-refresh';
COMMENT ON COLUMN matches.round_type IS 'round_robin, qf (quarter-final), sf (semi-final), final';
COMMENT ON COLUMN match_stats.checkout_percentage IS 'Auto-calculated: (checkouts_hit/checkouts_opportunities)*100';

-- ============================================================================
-- SCHEMA COMPLETE
-- ============================================================================
