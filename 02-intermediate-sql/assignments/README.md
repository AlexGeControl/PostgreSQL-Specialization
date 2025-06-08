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
# Database: pg4e_87d51122eb 
# User:     pg4e_87d51122eb 
# Password: pg4e_p_92c9c1bc0099645
docker run -it --rm -v $PWD/assignments/scripts:/workspace postgres psql -h pg.pg4e.com -p 5432 -U pg4e_87d51122eb pg4e_87d51122eb
```

---

## Module 1

### Q1. ALTER TABLE 

Add a new column **neon879** of data type **INTEGER** into the **pg4e_debug**

```pgsql
ALTER TABLE pg4e_debug
ADD COLUMN neon879 INTEGER;
```

### Q2. GROUP BY

```pgsql
-- 
SELECT 
    abbrev, 
    COUNT(name) AS count 
FROM pg_timezone_names 
WHERE is_dst = 't' 
GROUP BY abbrev HAVING COUNT(name) > 10 
ORDER BY count DESC;

```

### Q3. SELECT DISTINCT

```pgsql
SELECT DISTINCT state FROM taxdata ORDER BY state ASC LIMIT 5;
```

### Q4. Stored Procedure for Automatic updated_at Setting

The solution script is available at [here](scripts/auto-updated-at.sql)

```bash
# Host:     pg.pg4e.com 
# Port:     5432 
# Database: pg4e_87d51122eb 
# User:     pg4e_87d51122eb 
# Password: pg4e_p_92c9c1bc0099645
docker run -it --rm -v $PWD/scripts:/scripts postgres psql -h pg.pg4e.com -p 5432 -U pg4e_87d51122eb pg4e_87d51122eb
```

```pgsql
pg4e_87d51122eb=> \i /scripts/auto-updated-at.sql 
CREATE TABLE
CREATE FUNCTION
CREATE TRIGGER
```

---

## Module 3

### Generating Text

See the PGSQL script at [here](scripts/generate-text.sql)

---

## Module 3

### Q1. Regex Match

- **Target Pattern** Lines that end with with 4 or more digits

```bash
# connect to target database:
# Host:     pg.pg4e.com 
# Port:     5432 
# Database: readonly 
# User:     readonly 
# Password: secret_pg4e
docker run -it --rm -v $PWD/scripts:/scripts postgres psql -h pg.pg4e.com -p 5432 -U readonly readonly
```

Target table schema:

```pgsql
readonly=# \d+ taxdata
  Column  |          Type          |
----------+------------------------+
 id       | integer                |
 ein      | integer                |
 name     | character varying(255) |
 year     | integer                |
 revenue  | bigint                 |
 expenses | bigint                 |
 purpose  | text                   |
 ptid     | character varying(255) |
 ptname   | character varying(255) |
 city     | character varying(255) |
 state    | character varying(255) |
 url      | character varying(255) |
```

The answer SQL statement is as follows:

```pgsql
SELECT purpose FROM taxdata WHERE purpose ~ '^.*(\d{4,})$';
```