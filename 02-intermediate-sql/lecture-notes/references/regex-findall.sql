-- create tweet table
DROP TABLE IF EXISTS tweet;

CREATE TABLE tweet (
    id SERIAL, 
    tweet TEXT,
    PRIMARY KEY(ID)
);

INSERT INTO tweet (tweet) VALUES
    ('This is #SQL and #FUN stuff!'),
    ('More people should learn #SQL from #CMU!'),
    ('#CMU also teaches #Database!');

-- find all hashtags in tweet
SELECT 
    id, 
    REGEXP_MATCHES(tweet, '#[A-Za-z0-9]+', 'g') AS hashtag
FROM 
    tweet;