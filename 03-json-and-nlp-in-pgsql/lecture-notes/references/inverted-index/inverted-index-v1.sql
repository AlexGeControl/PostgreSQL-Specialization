
-- Adapted from https://www.pg4e.com/lectures/05-FullText.sql

-- Create documents table
DROP TABLE IF EXISTS docs CASCADE;
CREATE TABLE docs (
  id SERIAL, 
  doc TEXT, 
  PRIMARY KEY(id)
);

-- The GIN (General Inverted Index) thinks about columns that contain arrays
-- A GIN needs to know what kind of data will be in the arrays
-- array_ops means that it is expecting text[] (arrays of strings)
-- and WHERE clauses will use array operators (i.e. like <@ )
DROP INDEX IF EXISTS idx_docs_gin CASCADE;
CREATE INDEX idx_docs_gin ON docs USING gin(string_to_array(doc, ' ')  array_ops);

INSERT INTO docs (doc) VALUES
  ('This is SQL and Python and other fun teaching stuff'),
  ('More people should learn SQL from UMSI'),
  ('UMSI also teaches Python and also SQL');

-- Insert enough lines to get PostgreSQL attention
INSERT INTO docs (doc) 
  (
    SELECT 'Neon ' || generate_series(100000,200000)
  );

-- You might need to wait a minute until the index catches up to the inserts

-- The <@ if "is contained within" or "intersection" from set theory
SELECT 
  id, doc 
FROM 
  docs 
WHERE '{learn}' <@ string_to_array(doc, ' ');

-- Check whether the GIN is being used after PostgreSQL catches up
EXPLAIN (
  SELECT 
    id, doc 
  FROM 
    docs 
  WHERE 
    '{learn}' <@ string_to_array(doc, ' ')
);