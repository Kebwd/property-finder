-- Add source_url column to business table for store enhancement
ALTER TABLE business ADD COLUMN source_url TEXT;

-- Add source_url column to house table (for consistency)  
ALTER TABLE house ADD COLUMN source_url TEXT;

-- Add indexes for better performance on URL searches  
CREATE INDEX idx_business_source_url ON business(source_url);
CREATE INDEX idx_house_source_url ON house(source_url);
