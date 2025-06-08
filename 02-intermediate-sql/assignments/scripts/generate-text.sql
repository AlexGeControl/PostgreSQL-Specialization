-- This script creates a table for storing text data with an index for efficient searching
DROP TABLE IF EXISTS bigtext;

CREATE TABLE bigtext (
    id SERIAL,
    content TEXT,
    PRIMARY KEY(id)
);

-- Create an index on the content column for faster text searches
CREATE INDEX idx_bigtext_content ON bigtext(content);

-- Insert random URLs into the text_table
INSERT INTO bigtext (content)
SELECT 'This is record number ' || GENERATE_SERIES(100000, 199999)::TEXT || ' of quite a few text records.';