-- Create documents table
DROP TABLE IF EXISTS docs02 CASCADE;
CREATE TABLE docs02 (
    id SERIAL, 
    doc TEXT, 
    PRIMARY KEY(id)
);

-- Create the inverted index as lookup table
DROP TABLE IF EXISTS invert02 CASCADE;
CREATE TABLE invert02 (
    doc_id INTEGER REFERENCES docs02(id) ON DELETE CASCADE,
    keyword TEXT
);

-- Create the stop words table
DROP TABLE IF EXISTS stop_words CASCADE;
CREATE TABLE stop_words (
    word TEXT UNIQUE
);

-- Insert stop words into the stop words table
INSERT INTO stop_words (word) VALUES 
    ('i'), 
    ('a'), 
    ('about'), 
    ('an'), 
    ('are'), 
    ('as'), 
    ('at'), 
    ('be'), 
    ('by'), 
    ('com'), 
    ('for'), 
    ('from'), 
    ('how'), 
    ('in'), 
    ('is'), 
    ('it'), 
    ('of'), 
    ('on'), 
    ('or'), 
    ('that'), 
    ('the'), 
    ('this'), 
    ('to'), 
    ('was'), 
    ('what'), 
    ('when'), 
    ('where'), 
    ('who'), 
    ('will'), 
    ('with');

-- Insert sample documents
INSERT INTO docs02 (doc) VALUES
    ('memory are disk drives or flash memory typically found in USB'),
    ('sticks and portable music players'),
    ('keyboard mouse microphone speaker touchpad etc They are all of'),
    ('the ways we interact with the computer'),
    ('Connection to retrieve information over a network We can'),
    ('think of the network as a very slow place to store and retrieve data'),
    ('that might not always be up So in a sense the network is a'),
    ('slower and at times unreliable form of Secondary'),
    ('While most of the detail of how these components work is best left to'),
    ('computer builders it helps to have some terminology so we can talk');

-- Insert the keywords, with stop words removed, into the inverted index
INSERT INTO invert02 (doc_id, keyword)
    (
        SELECT DISTINCT id, s.keyword AS keyword
        FROM docs02 AS D, unnest(string_to_array(lower(D.doc), ' ')) s(keyword)
        WHERE keyword NOT IN (SELECT word FROM stop_words)
        ORDER BY id
    );

-- Inspect the inverted index
SELECT 
    keyword, doc_id 
FROM 
    invert02 
ORDER BY keyword, doc_id 
LIMIT 10;