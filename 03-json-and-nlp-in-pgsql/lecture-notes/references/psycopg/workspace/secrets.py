# Keep this file separate

# https://www.pg4e.com/code/hidden-dist.py

# psql -h pg.pg4e.com -p 5432 -U pg4e_be9e729093 pg4e_be9e729093

# %load_ext sql
# %config SqlMagic.autocommit=False
# %sql postgresql://pg4e_be9e729093:pg4e_p_d5fab7440699124@pg.pg4e.com:5432/pg4e_be9e729093
# %sql SELECT 1 as "Test"
from typing import TypeAlias

ConnectionParams: TypeAlias = dict[str, str | int]


def elastic() -> ConnectionParams:
    """Returns connection parameters for the Elasticsearch database in pg4e.com
    Returns:
        ConnectionParams: A dictionary containing Elasticsearch connection parameters:
            - host (str): The Elasticsearch server hostname
            - prefix (str): The Elasticsearch index prefix
            - port (int): The Elasticsearch server port number
            - scheme (str): The protocol scheme (http or https)
            - user (str): The username for authentication
            - pass (str): The password for authentication
    """
    return {"host": "www.pg4e.com",
            "prefix" : "elasticsearch",
            "port": 443,
            "scheme": "https",
            "user": "pg4e_86f9be92a2",
            "pass": "2008_9d454b1f"}


def postgres_read_write() -> ConnectionParams:
    """Returns connection parameters for the read-write PostgreSQL database in pg4e.com
    
    Returns:
        ConnectionParams: A dictionary containing database connection parameters:
            - host (str): The database server hostname
            - port (int): The database server port number
            - database (str): The database name to connect to
            - user (str): The username for authentication
            - pass (str): The password for authentication
    """
    return {"host": "pg.pg4e.com",
            "port": 5432,
            "database": "pg4e_b0429fdfdf",
            "user": "pg4e_b0429fdfdf",
            "pass": "pg4e_p_63e777959d7b58a"}


def postgres_readonly() -> ConnectionParams:
    """Returns connection parameters for the read-only PostgreSQL database in pg4e.com
    
    Returns:
        ConnectionParams: A dictionary containing database connection parameters:
            - host (str): The database server hostname
            - port (int): The database server port number
            - database (str): The database name to connect to
            - user (str): The username for authentication
            - pass (str): The password for authentication
    """
    return {"host": "pg.pg4e.com",
            "port": 5432,
            "database": "readonly",
            "user": "readonly",
            "pass": "readonly_password"}


def postgres_local() -> ConnectionParams:
    """Returns connection parameters for the read-write local PostgreSQL database in pg4e.com
    
    Returns:
        ConnectionParams: A dictionary containing database connection parameters:
            - host (str): The database server hostname
            - port (int): The database server port number
            - database (str): The database name to connect to
            - user (str): The username for authentication
            - pass (str): The password for authentication
    """
    return {"host": "localhost",
            "port": 5432,
            "database": "text",
            "user": "postgres",
            "pass": "postgres"}


def psycopg_connection_string(secrets: ConnectionParams) -> str:
    """Generates a psycopg connection string from the provided secrets.
    Args:
        secrets (ConnectionParams): A dictionary containing database connection parameters.
    Returns:
        str: A formatted connection string for psycopg.
    """
    if not all(key in secrets for key in ['user', 'pass', 'host', 'port', 'database']):
        raise ValueError("Missing required keys in secrets dictionary")
    
    return (
        f"dbname={secrets['database']} " 
        f"user={secrets['user']} "
        f"password={secrets['pass']} "
        f"host={secrets['host']} "
        f"port={secrets['port']}"
    )


def postgres_sqlalchemy_connection_string(secrets: ConnectionParams) -> str:
    """Generates a SQLAlchemy connection string for PostgreSQL from the provided secrets.
    Args:
        secrets (ConnectionParams): A dictionary containing database connection parameters.
    Returns:
        str: A formatted SQLAlchemy connection string for PostgreSQL.
    """
    if not all(key in secrets for key in ['user', 'pass', 'host', 'port', 'database']):
        raise ValueError("Missing required keys in secrets dictionary")
    
    return (
        f"postgresql://{secrets['user']}:{secrets['pass']}@{secrets['host']}:{secrets['port']}/{secrets['database']}"
    )


if __name__ == "__main__":
    # Unit tests for PostgreSQL connection strings
    assert psycopg_connection_string(postgres_read_write()) == "dbname=pg4e_b0429fdfdf user=pg4e_b0429fdfdf password=pg4e_p_63e777959d7b58a host=pg.pg4e.com port=5432", "Psycopg connection string is incorrect"
    print("[Psycopg Connection String Check]: Passed")
    assert postgres_sqlalchemy_connection_string(postgres_read_write()) == "postgresql://pg4e_b0429fdfdf:pg4e_p_63e777959d7b58a@pg.pg4e.com:5432/pg4e_b0429fdfdf", "PostgreSQL SQLAlchemy connection string is incorrect"
    print("[PostgreSQL SQLAlchemy Connection String Check]: Passed")