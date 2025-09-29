-- AceWatch Database Initialization Script
-- This script creates the initial database structure for the AceWatch tennis monitoring system

-- Create database if not exists (handled by docker-compose)
-- The database 'acewatch_db' is created automatically by the PostgreSQL container

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create matches table
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    external_event_id VARCHAR(255) UNIQUE NOT NULL,
    league VARCHAR(255) NOT NULL,
    round VARCHAR(255),
    home_player VARCHAR(255) NOT NULL,
    away_player VARCHAR(255) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'Scheduled',
    score_json JSONB,
    last_fetch_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create favorites table
CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    external_player_id VARCHAR(255),
    external_event_id VARCHAR(255),
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('player', 'match')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    trigger VARCHAR(100) NOT NULL CHECK (trigger IN ('match_started', 'tie_break', 'third_set', 'match_finished')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_matches_external_event_id ON matches(external_event_id);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
CREATE INDEX IF NOT EXISTS idx_matches_start_time ON matches(start_time);
CREATE INDEX IF NOT EXISTS idx_matches_league ON matches(league);

CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_type ON favorites(type);
CREATE INDEX IF NOT EXISTS idx_favorites_external_player_id ON favorites(external_player_id);
CREATE INDEX IF NOT EXISTS idx_favorites_external_event_id ON favorites(external_event_id);
CREATE INDEX IF NOT EXISTS idx_favorites_match_id ON favorites(match_id);

CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_match_id ON alerts(match_id);
CREATE INDEX IF NOT EXISTS idx_alerts_is_active ON alerts(is_active);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Insert demo user for testing
INSERT INTO users (email, password_hash) VALUES 
    ('test@acewatch.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewUxwrQ6fQV8d8H6')  -- password: test123
ON CONFLICT (email) DO NOTHING;

-- Note: Real match data will be populated by the Scores Service from TheSportsDB API

-- Create a function to automatically update last_fetch_at
CREATE OR REPLACE FUNCTION update_last_fetch_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_fetch_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update last_fetch_at on matches table
DROP TRIGGER IF EXISTS trigger_update_matches_last_fetch_at ON matches;
CREATE TRIGGER trigger_update_matches_last_fetch_at
    BEFORE UPDATE ON matches
    FOR EACH ROW
    EXECUTE FUNCTION update_last_fetch_at();

-- Create a view for active matches with user favorites
CREATE OR REPLACE VIEW active_matches_view AS
SELECT 
    m.*,
    COUNT(f.id) as favorite_count
FROM matches m
LEFT JOIN favorites f ON m.id = f.match_id AND f.type = 'match'
WHERE m.status IN ('Scheduled', 'In Play')
GROUP BY m.id
ORDER BY m.start_time ASC;

-- Create a view for match statistics
CREATE OR REPLACE VIEW match_statistics_view AS
SELECT 
    league,
    COUNT(*) as total_matches,
    COUNT(CASE WHEN status = 'Scheduled' THEN 1 END) as scheduled_matches,
    COUNT(CASE WHEN status = 'In Play' THEN 1 END) as live_matches,
    COUNT(CASE WHEN status = 'Finished' THEN 1 END) as finished_matches
FROM matches
GROUP BY league
ORDER BY total_matches DESC;

-- Create a function to clean old finished matches (optional maintenance)
CREATE OR REPLACE FUNCTION clean_old_matches(days_old INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM matches 
    WHERE status = 'Finished' 
    AND last_fetch_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_old;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions to the acewatch user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO acewatch;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO acewatch;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO acewatch;

-- Log successful initialization
INSERT INTO matches (external_event_id, league, round, home_player, away_player, status) VALUES 
    ('db_init_marker', 'SYSTEM', 'Database Initialization', 'AceWatch', 'PostgreSQL', 'Finished')
ON CONFLICT (external_event_id) DO NOTHING;
