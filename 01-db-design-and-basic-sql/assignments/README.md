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

---

## Module 3

In this assignment we'll populate an automobile dealer's database

### Schema Defintion

```pgsql
CREATE TABLE make (
    id SERIAL,
    name VARCHAR(128) UNIQUE,
    PRIMARY KEY(id)
);

CREATE TABLE model (
  id SERIAL,
  name VARCHAR(128),
  make_id INTEGER REFERENCES make(id) ON DELETE CASCADE,
  PRIMARY KEY(id)
);
```

### Data Population

```pgsql
/* populate make */
INSERT INTO make (name) VALUES ('Mercedes-Benz');
INSERT INTO make (name) VALUES ('Suzuki');
/* populate model */
INSERT INTO model (name, make_id) VALUES ('CLS400 4matic', 1);
INSERT INTO model (name, make_id) VALUES ('CLS450', 1);
INSERT INTO model (name, make_id) VALUES ('CLS450 4matic', 1);
INSERT INTO model (name, make_id) VALUES ('SX4 Sport', 2);
INSERT INTO model (name, make_id) VALUES ('SX4 Sport/Anniversary Edition', 2);
```

### Sanity Check

```pgsql
SELECT make.name, model.name
    FROM model
    JOIN make ON model.make_id = make.id
    ORDER BY make.name LIMIT 5;
```

### Test Suite Inspection

```pgsql
SELECT query, result, created_at FROM pg4e_debug;
```

---

## Module 4

In this assignment we'll normalize one online education dataset according to the given data model

### Data Schema

```pgsql
DROP TABLE student CASCADE;
CREATE TABLE student (
    id SERIAL,
    name VARCHAR(128) UNIQUE,
    PRIMARY KEY(id)
);

DROP TABLE course CASCADE;
CREATE TABLE course (
    id SERIAL,
    title VARCHAR(128) UNIQUE,
    PRIMARY KEY(id)
);

DROP TABLE roster CASCADE;
CREATE TABLE roster (
    id SERIAL,
    student_id INTEGER REFERENCES student(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES course(id) ON DELETE CASCADE,
    role INTEGER,
    UNIQUE(student_id, course_id),
    PRIMARY KEY (id)
);
```

### Application Requirements

Below is the target dataset from [section.csv](data/section.csv)

```csv
Esha, si106, Instructor
Aila, si106, Learner
Codi, si106, Learner
Jamieleigh, si106, Learner
Laaibah, si106, Learner
Keilan, si110, Instructor
Ijay, si110, Learner
Nikolina, si110, Learner
Ninon, si110, Learner
Shanzay, si110, Learner
Mikhail, si206, Instructor
Ailey, si206, Learner
Aleese, si206, Learner
Malayka, si206, Learner
Sharona, si206, Learner
```

### Rule-Based SQL Generation

```python
import pandas as pd

# Load section dataset
df = pd.read_csv('data/section.csv', header=None, names=['student', 'course', 'role'])

# Encode student
student_code, student_unique = pd.factorize(df['student'])
df['student_id'] = student_code + 1

# Populate student
print(
    "\n".join(
        f"INSERT INTO student (name) VALUES ('{student}');" for student in student_unique.values
    )
)

# Encode course
course_code, course_unique = pd.factorize(df['course'].apply(lambda x: x.strip()))
df['course_id'] = course_code + 1

# Populate course
print(
    "\n".join(
        f"INSERT INTO course (title) VALUES ('{course}');" for course in course_unique.values
    )
)

# Encode role
role_code, role_unique = pd.factorize(df['role'].apply(lambda x: x.strip()))
df['role_id'] = 1 - role_code

# Populate roster
print(
    "\n".join(
        f"INSERT INTO roster (student_id, course_id, role) VALUES ({row.student_id}, {row.course_id}, {row.role_id});" for _, row in df.iterrows()
    )
)
```

### Student Population

```pgsql
INSERT INTO student (name) VALUES ('Esha');
INSERT INTO student (name) VALUES ('Aila');
INSERT INTO student (name) VALUES ('Codi');
INSERT INTO student (name) VALUES ('Jamieleigh');
INSERT INTO student (name) VALUES ('Laaibah');
INSERT INTO student (name) VALUES ('Keilan');
INSERT INTO student (name) VALUES ('Ijay');
INSERT INTO student (name) VALUES ('Nikolina');
INSERT INTO student (name) VALUES ('Ninon');
INSERT INTO student (name) VALUES ('Shanzay');
INSERT INTO student (name) VALUES ('Mikhail');
INSERT INTO student (name) VALUES ('Ailey');
INSERT INTO student (name) VALUES ('Aleese');
INSERT INTO student (name) VALUES ('Malayka');
INSERT INTO student (name) VALUES ('Sharona');
```

### Course Population

```pgsql
INSERT INTO course (title) VALUES ('si106');
INSERT INTO course (title) VALUES ('si110');
INSERT INTO course (title) VALUES ('si206');
```

### Roster Population

```pgsql
INSERT INTO roster (student_id, course_id, role) VALUES (1, 1, 1);
INSERT INTO roster (student_id, course_id, role) VALUES (2, 1, 0);
INSERT INTO roster (student_id, course_id, role) VALUES (3, 1, 0);
INSERT INTO roster (student_id, course_id, role) VALUES (4, 1, 0);
INSERT INTO roster (student_id, course_id, role) VALUES (5, 1, 0);
INSERT INTO roster (student_id, course_id, role) VALUES (6, 2, 1);
INSERT INTO roster (student_id, course_id, role) VALUES (7, 2, 0);
INSERT INTO roster (student_id, course_id, role) VALUES (8, 2, 0);
INSERT INTO roster (student_id, course_id, role) VALUES (9, 2, 0);
INSERT INTO roster (student_id, course_id, role) VALUES (10, 2, 0);
INSERT INTO roster (student_id, course_id, role) VALUES (11, 3, 1);
INSERT INTO roster (student_id, course_id, role) VALUES (12, 3, 0);
INSERT INTO roster (student_id, course_id, role) VALUES (13, 3, 0);
INSERT INTO roster (student_id, course_id, role) VALUES (14, 3, 0);
INSERT INTO roster (student_id, course_id, role) VALUES (15, 3, 0);
```

### Sanity Check

```pgsql
SELECT student.name, course.title, roster.role
    FROM student 
    JOIN roster ON student.id = roster.student_id
    JOIN course ON roster.course_id = course.id
    ORDER BY course.title, roster.role DESC, student.name;
```