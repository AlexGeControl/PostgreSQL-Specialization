-- Create documents table
DROP TABLE IF EXISTS docs cascade;
CREATE TABLE docs (
    id SERIAL, 
    doc TEXT, 
    PRIMARY KEY(id)
);

-- Create GIN inverted index
DROP INDEX idx_docs_gin CASCADE;
CREATE INDEX idx_docs_gin ON docs USING gin(to_tsvector('english', doc));

-- Insert sample documents
INSERT INTO docs (doc) VALUES
    ('This is SQL and Python and other fun teaching stuff'),
    ('More people should learn SQL from UMSI'),
    ('UMSI also teaches Python and also SQL');

INSERT INTO docs (doc) SELECT 'Neon ' || generate_series(10000,20000);

-- Wait for the index to be created

-- Query the documents using the inverted index 
SELECT id, doc FROM docs WHERE
    to_tsquery('english', 'learn') @@ to_tsvector('english', doc);

EXPLAIN SELECT id, doc FROM docs WHERE
    to_tsquery('english', 'learn') @@ to_tsvector('english', doc);