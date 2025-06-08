/*
  Inverted index with stop words filtering and stemming in PostgreSQL
  
  If we know the documents contain natural language, we can optimize indexes as follows:

    (1) Ignore the case of words in the index and in the query
    (2) Don't index low-meaning "stop words" that we will ignore
    (3) Only store the "stems" of words

  if they are in a search query
*/
-- Create documents table
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

-- Create stop words table
DROP TABLE IF EXISTS stop_words CASCADE;
CREATE TABLE stop_words (
  word TEXT unique
);

INSERT INTO stop_words (word) VALUES 
  ('is'), 
  ('this'), 
  ('and');

-- Create word_stems table
DROP TABLE IF EXISTS word_stems CASCADE;
CREATE TABLE word_stems (
  word TEXT, 
  stem TEXT
);

INSERT INTO word_stems (word, stem) VALUES
  ('teaching', 'teach'), 
  ('teaches', 'teach');

-- Create inverted index table
DROP TABLE IF EXISTS idx_docs_gin CASCADE;
CREATE TABLE idx_docs_gin (
  doc_id INTEGER REFERENCES docs(id) ON DELETE CASCADE,
  keyword TEXT
);

-- Populate the inverted index table
INSERT INTO idx_docs_gin (doc_id, keyword) 
(
  SELECT 
    id,
    -- For each keyword, if it has a stem, use the stem, otherwise use the keyword 
    COALESCE(stem, keyword)
  FROM (
    SELECT 
      DISTINCT id, s.keyword AS keyword
    FROM docs AS D, unnest(string_to_array(lower(D.doc), ' ')) s(keyword)
    -- Stop words filtering
    WHERE s.keyword NOT IN (SELECT word FROM stop_words)
  ) AS K
    -- Associate the keyword with its stem if it exists
    LEFT JOIN word_stems AS S ON K.keyword = S.word
);

-- Inspect the inverted index table
SELECT 
  doc_id, keyword 
FROM idx_docs_gin
ORDER BY doc_id, keyword;

-- Query the inverted index for documents containing either the word sten of "teaching" or the key word "teaching"
SELECT 
  DISTINCT id, doc 
FROM docs AS D
  JOIN idx_docs_gin AS G ON D.id = G.doc_id
WHERE 
  G.keyword = COALESCE((SELECT stem FROM word_stems WHERE word=lower('teaching')), lower('teaching'));