
-- Adapted from https://www.pg4e.com/lectures/05-FullText.sql

-- The utility functions for building inverted index
SELECT string_to_array('Hello world', ' ');
SELECT unnest(string_to_array('Hello world', ' '));

-- Generate docuemnts
DROP TABLE IF EXISTS docs CASCADE;
CREATE TABLE docs (
  id SERIAL, 
  doc TEXT, 
  PRIMARY KEY(id)
);

INSERT INTO docs (doc) VALUES
  ('This is SQL and Python and other fun teaching stuff'),
  ('More people should learn SQL from UMSI'),
  ('UMSI also teaches Python and also SQL');

-- Inspect the documents
SELECT * FROM docs;


SELECT DISTINCT id, s.keyword AS keyword
FROM docs AS D, unnest(string_to_array(D.doc, ' ')) s(keyword)
ORDER BY id;

-- Create a table to hold the inverted index
-- For a lookup table like this, we don't need a primary key
DROP TABLE IF EXISTS docs_gin cascade;
CREATE TABLE idx_docs_gin (
  doc_id INTEGER REFERENCES docs(id) ON DELETE CASCADE,
  keyword TEXT
);

-- Insert the keywords into the inverted index
-- This is a "cross join lateral" that breaks the document into a bag of words
INSERT INTO idx_docs_gin (doc_id, keyword)
  (
    /* 
      Use implicit cross lateral join to break the document into bag of words
      It is equivalent to the following query:
       
        SELECT DISTINCT id, s.keyword AS keyword
        FROM docs AS D
          CROSS JOIN LATERAL unnest(string_to_array(D.doc, ' ')) s(keyword)
        ORDER BY id;
    */
    SELECT DISTINCT id, s.keyword AS keyword
    FROM docs AS D, unnest(string_to_array(D.doc, ' ')) s(keyword)
    ORDER BY id
  );

-- Inspect the inverted index
SELECT * FROM idx_docs_gin ORDER BY doc_id;

-- Query with a single keyword
SELECT 
  DISTINCT id, doc 
FROM docs AS D
  JOIN idx_docs_gin AS G ON D.id = G.doc_id
WHERE G.keyword = 'UMSI';

-- We can use more than one keyword by providing a set of keywords explicitly
SELECT 
  DISTINCT doc 
FROM docs AS D
  JOIN idx_docs_gin AS G ON D.id = G.doc_id
WHERE G.keyword IN ('fun', 'people');

-- We can also query with a phrase by breaking it into words
-- and using the ANY operator
SELECT 
  DISTINCT doc 
FROM docs AS D
  JOIN idx_docs_gin AS G ON D.id = G.doc_id
WHERE G.keyword = ANY(string_to_array('I want to learn', ' '));
