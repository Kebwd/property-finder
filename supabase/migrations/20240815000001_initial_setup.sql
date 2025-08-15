-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create stores table
CREATE TABLE stores (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  address TEXT NOT NULL,
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  deal_date DATE,
  category TEXT,
  deal_price NUMERIC(10,2),
  geom GEOGRAPHY(Point,4326),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create function to set geometry from lat/lng
CREATE OR REPLACE FUNCTION set_geom() RETURNS trigger AS $$
BEGIN
  NEW.geom := ST_SetSRID(
    ST_MakePoint(NEW.longitude, NEW.latitude), 4326
  )::geography;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically set geometry
CREATE TRIGGER trg_set_geom
  BEFORE INSERT OR UPDATE ON stores
  FOR EACH ROW EXECUTE PROCEDURE set_geom();

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_stores_updated_at
  BEFORE UPDATE ON stores
  FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Create indexes for better performance
CREATE INDEX idx_stores_geom ON stores USING GIST(geom);
CREATE INDEX idx_stores_category ON stores(category);
CREATE INDEX idx_stores_deal_date ON stores(deal_date);
CREATE INDEX idx_stores_location ON stores(latitude, longitude);

-- Enable Row Level Security (RLS)
ALTER TABLE stores ENABLE ROW LEVEL SECURITY;

-- Create policy to allow read access to all users
CREATE POLICY "Allow read access to stores" ON stores
  FOR SELECT USING (true);

-- Create policy to allow insert/update/delete for authenticated users
CREATE POLICY "Allow all operations for authenticated users" ON stores
  FOR ALL USING (auth.role() = 'authenticated');
