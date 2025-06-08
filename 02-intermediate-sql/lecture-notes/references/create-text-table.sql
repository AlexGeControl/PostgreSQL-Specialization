-- This script creates a table for storing text data with an index for efficient searching
DROP TABLE IF EXISTS corpora;

CREATE TABLE corpora (
    id SERIAL,
    url TEXT,
    content TEXT,
    PRIMARY KEY(id)
);

-- Create an unique index on the url column to prevent duplicated page crawls
CREATE UNIQUE INDEX idx_corpora_url ON corpora(md5(url));

-- Evaluate index usage 
SELECT 
    pg_relation_size('corpora') AS table_size,
    pg_indexes_size('corpora') AS index_size;

-- Insert random URLs into the corpora table
INSERT INTO corpora (url, content)
    SELECT 
        (
            CASE WHEN RANDOM() < 0.5 THEN 
                'https://www.pg4e.com/neon/'
            ELSE
                'https://www.pg4e.com/lemon/'
            END
        ) || GENERATE_SERIES(100000, 200000)::TEXT AS url,
        md5(GENERATE_SERIES(100000, 200000)::TEXT) AS content;

-- Evaluate index usage 
SELECT 
    pg_relation_size('corpora') AS table_size,
    pg_indexes_size('corpora') AS index_size;

-- Compare two queries for URL retrieval
-- The first query doesn't use the index on the url column, while the second query does use the index
EXPLAIN ANALYZE
SELECT * FROM corpora WHERE url = 'https://www.pg4e.com/neon/100000';

EXPLAIN ANALYZE
SELECT * FROM corpora WHERE md5(url) = md5('https://www.pg4e.com/neon/100000');

-- Inser a new URL uuid column into the corpora table
ALTER TABLE corpora 
    ADD COLUMN uuid UUID UNIQUE;

UPDATE corpora 
    SET uuid = md5(url)::UUID;

-- Evaluate index usage 
SELECT 
    pg_relation_size('corpora') AS table_size,
    pg_indexes_size('corpora') AS index_size;

-- Switch to hash index for url column
DROP INDEX IF EXISTS idx_corpora_url;
CREATE INDEX idx_corpora_url ON corpora USING HASH (url);

-- Evaluate index usage 
SELECT 
    pg_relation_size('corpora') AS table_size,
    pg_indexes_size('corpora') AS index_size;

-- Compare two queries for URL retrieval
-- Both queries now use the indices
-- For equality checks, the hash index has comparable retrieval performance to the btree index, but it is more spatially efficient
EXPLAIN ANALYZE
SELECT * FROM corpora WHERE url = 'https://www.pg4e.com/neon/100000';

EXPLAIN ANALYZE
SELECT * FROM corpora WHERE uuid = md5('https://www.pg4e.com/neon/100000')::UUID;
