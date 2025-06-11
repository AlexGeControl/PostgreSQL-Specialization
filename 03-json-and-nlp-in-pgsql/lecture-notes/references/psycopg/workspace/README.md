# Introduction to Python PostgreSQL Connector

---

## Set Up PostgreSQL Client

Use the docker command below to connect to the local PostgreSQL instance:

```bash
# Host:     pgsql-server
# Port:     5432 
# Database: text 
# User:     postgres 
# Password: postgres
docker run -it --rm --network postgres-network postgres psql -h pgsql-server -p 5432 -U postgres
```

Use the docker command below to connect to the PostgreSQL instance in pg4e.com:

```bash
# Host:     pg.pg4e.com 
# Port:     5432 
# Database: pg4e_b0429fdfdf 
# User:     pg4e_b0429fdfdf 
# Password: pg4e_p_63e777959d7b58a
docker run -it --rm postgres psql -h pg.pg4e.com -p 5432 -U pg4e_b0429fdfdf pg4e_b0429fdfdf
```

---

## Topics

- [Introduction to Psycopg](introduction-to-psycopg.py)
- [Index Project Gutenberg](index-gutenberg.py)
- [Index Mail](index-mails.py)