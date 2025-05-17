# Assignments

---

## Connect to Course Database

### Set Up Docker

The content below is based on [this tutorial](https://www.docker.com/blog/how-to-use-the-postgres-docker-official-image/#Why-should-you-containerize-Postgres)

```bash
# fetch official image
docker pull postgres
# create network for client-server communication
docker network create postgres-network
# launch pgsql server in detached mode
# --name pgsql-server: name the container instance as pgsql-server
# --network postgres-network: attach the container to the specific network postgres-network
# -e POSTGRES_PASSWORD=postgres: during initialization, the super user postgres will be created. 
#                                its password is configured through this env var
# -d: run in detached mode
# postgres: using image postgres
docker run --name pgsql-server --network postgres-network -e POSTGRES_PASSWORD=postgres -d postgres
# connect with psql cli
# --name pgsql-server: name the container instance as pgsql-server
# --network postgres-network: attach the container to the specific network postgres-network
# -e POSTGRES_PASSWORD=postgres: during initialization, the super user postgres will be created. 
#                                its password is configured through this env var
# -d: run in detached mode
# --rm: automatically removes the container instance when it exits
# -it: runs the container interactively with a terminal
# --network postgres-network: attach the container to the specific network postgres-network
# postgres: using image postgres, which contains the psql client
# psql -h pgsql-server -U postgres: login to psql server pgsql-server using super user postgres
docker run -it --rm --network postgres-network postgres psql -h pgsql-server -U postgres
```

### Launch psql in Docker

```bash
# Host:     pg.pg4e.com 
# Port:     5432 
# Database: pg4e_47e3719f9b 
# User:     pg4e_47e3719f9b 
# Password: pg4e_p_71d82231c49466b
docker run -it --rm postgres psql -h pg.pg4e.com -p 5432 -U pg4e_47e3719f9b pg4e_47e3719f9b
```

---

## Module 2

### Q1. SERIAL fields / Auto Increment

Create a table named automagic with the following fields: 

- An **id** field that is an **auto-incrementing serial field**. 

- A **name** field that allows **up to 32 characters** but no more. This field is required. 

- A **height** field that is a **floating point number** that is required. 

```pgsql
CREATE TABLE automagic (
    id SERIAL,
    name VARCHAR(32) NOT NULL,
    height REAL NOT NULL,
    PRIMARY KEY (id)
);
```

```pgsql
SELECT query, result, created_at FROM pg4e_debug;
```

### Q2. SERIAL fields / Auto Increment

#### Download Data

```bash
wget https://www.pg4e.com/tools/sql/library.csv
```

#### Define Schema

```pgsql
CREATE TABLE track_raw (
    title TEXT,
    artist TEXT,
    album TEXT,
    count INTEGER,
    rating INTEGER,
    len INTEGER
);
```

#### Load CSV

Below is the server-side command:

```pgsql
COPY track_raw (
    title,
    artist,
    album,
    count,
    rating,
    len
) FROM '/data/library.csv'
WITH (
    FORMAT csv,
    DELIMITER ',',
);
```

Below is the client-side command:

```pgsql
\copy track_raw (
    title,
    artist,
    album,
    count,
    rating,
    len
) FROM '/data/library.csv'
WITH (
    FORMAT csv,
    DELIMITER ',',
);
```

#### Sanity Check

```pgsql
SELECT 
    title, album 
FROM 
    track_raw 
ORDER BY 
    title 
LIMIT 3;
```

#### Test Suite Inspection

```pgsql
SELECT query, result, created_at FROM pg4e_debug;
```
