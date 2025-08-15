CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE stores (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  address TEXT NOT NULL,
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  deal_date DATE,
  category TEXT,
  deal_price NUMERIC(10,2),
  geom GEOGRAPHY(Point,4326)
);

CREATE FUNCTION set_geom() RETURNS trigger AS $$
BEGIN
  NEW.geom := ST_SetSRID(
    ST_MakePoint(NEW.longitude, NEW.latitude), 4326
  )::geography;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_set_geom
  BEFORE INSERT OR UPDATE ON stores
  FOR EACH ROW EXECUTE PROCEDURE set_geom();