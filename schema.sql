-- Create table for reports
CREATE TABLE environmental_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lat FLOAT NOT NULL,
    lng FLOAT NOT NULL,
    rounded_lat FLOAT NOT NULL,
    rounded_lng FLOAT NOT NULL,
    issue_type TEXT NOT NULL,
    severity TEXT,
    description TEXT,
    symptom_tags JSONB,
    image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create table for AI analysis results
CREATE TABLE report_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID REFERENCES environmental_reports(id) ON DELETE CASCADE,
    embedding_id TEXT,
    similar_count INT DEFAULT 0,
    confidence_score FLOAT,
    ai_summary TEXT,
    risk_level TEXT
);

-- Create table for metadata (rate limiting/privacy)
CREATE TABLE report_meta (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID REFERENCES environmental_reports(id) ON DELETE CASCADE,
    ip_hash TEXT NOT NULL,
    session_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
