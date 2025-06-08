-- Create documents table
CREATE TABLE docs03 (
    id SERIAL, 
    doc TEXT, 
    PRIMARY KEY(id)
);

-- Create the inverted index using PostgreSQL GIN
CREATE INDEX array03 ON docs03 USING gin(string_to_array(lower(doc), ' ') array_ops);

-- Insert sample documents
INSERT INTO docs03 (doc) VALUES
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

-- Insert more sample documents to ensure the index will be used
INSERT INTO docs03 (doc) 
    (
        SELECT 'Neon ' || generate_series(10000,20000)
    );

-- Inspect the inverted index
EXPLAIN 
    (
        SELECT 
            id, doc 
        FROM 
            docs03 
        WHERE '{information}' <@ string_to_array(lower(doc), ' ')
    );