-- Create documents table
CREATE TABLE docs01 (
    id SERIAL, 
    doc TEXT, 
    PRIMARY KEY(id)
);

-- Create the inverted index as lookup table
CREATE TABLE invert01 (
    doc_id INTEGER REFERENCES docs01(id) ON DELETE CASCADE,
    keyword TEXT
);

-- Insert sample documents
INSERT INTO docs01 (doc) VALUES
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

-- Insert the keywords into the inverted index
INSERT INTO invert01 (doc_id, keyword)
    (
        SELECT DISTINCT id, s.keyword AS keyword
        FROM docs01 AS D, unnest(string_to_array(lower(D.doc), ' ')) s(keyword)
        ORDER BY id
    );

-- Inspect the inverted index
SELECT 
    keyword, doc_id 
FROM 
    invert01 
ORDER BY keyword, doc_id 
LIMIT 10;