import psycopg
from secrets import (
    postgres_read_write,
    psycopg_connection_string
)
from typing import Generator, Tuple


# Get connection string to the database:
def get_connection_string():
    """Generates a connection string for PostgreSQL using psycopg.
    
    Returns:
        str: A formatted connection string for psycopg.
    """
    conn_params = postgres_read_write()
    return psycopg_connection_string(conn_params)


def get_connection():
    """Establishes a connection to the PostgreSQL database using psycopg.
    
    Returns:
        Connection: A psycopg connection object.
    """
    conn_string = get_connection_string()
    return psycopg.connect(conn_string, autocommit=False, connect_timeout=3)


def create_table(table_name: str = 'pythonseq'):
    """Creates the sample table in the PostgreSQL database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            stmt = f'DROP TABLE IF EXISTS {table_name} CASCADE;'
            print(stmt)
            cur.execute(stmt)

            stmt = f'CREATE TABLE {table_name} (iter INTEGER, val INTEGER);'
            print(stmt)
            cur.execute(stmt)

            conn.commit()
            print("Table created successfully.")


def generate_pseudorandom_numbers(n: int) -> Generator[Tuple[int, int], None, None]:
    """Generates a list of n pseudorandom numbers"""
    val = 569340
    for iter in range(n):
        yield (iter+1, val)
        val = int((val * 22) / 7) % 1000000


def insert_pseudorandom_numbers_into_table(pseudorandom_numbers: Generator[Tuple[int, int], None, None], table_name: str = 'pythonseq'):
    """Inserts pseudorandom numbers into the table in the PostgreSQL database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            for indexed_pseudorandom_number in pseudorandom_numbers:
                print(f"Processing {repr(indexed_pseudorandom_number)}")
                
                stmt = f"INSERT INTO {table_name} (iter, val) VALUES (%s, %s);"
                cur.execute(stmt, indexed_pseudorandom_number)

                iter, _ = indexed_pseudorandom_number
                if iter % 100 == 0:
                    conn.commit()

            print(f'Inserted {iter + 1} pseudorandom numbers into table successfully.')


if __name__ == "__main__":
    # Create the table
    create_table()

    # Insert pseudorandom numbers into the table
    insert_pseudorandom_numbers_into_table(
        generate_pseudorandom_numbers(300),
        'pythonseq'
    )