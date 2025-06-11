import psycopg
from secrets import (
    postgres_read_write,
    psycopg_connection_string
)

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


def create_table():
    """Creates the sample table in the PostgreSQL database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            stmt = 'DROP TABLE IF EXISTS pythonfun CASCADE;'
            print(stmt)
            cur.execute(stmt)

            stmt = 'CREATE TABLE pythonfun (id SERIAL, line TEXT);'
            print(stmt)
            cur.execute(stmt)

            conn.commit()
            print("Table created successfully.")


def insert_row(line: str):
    """Inserts a single row into the pythonfun table."""
    if not line:
        raise ValueError("Line must not be empty.")
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            stmt = 'INSERT INTO pythonfun (line) VALUES (%s) RETURNING id;'
            cur.execute(stmt, (line,))
            # The ID of the newly inserted row will be available immediately
            # after the execute call, since we used RETURNING id.
            (id, ) = cur.fetchone()
            print(f"New row with ID: {id}")
            conn.commit()
            print("Row inserted successfully.")


def insert_rows():
    """Inserts sample rows into the pythonfun table."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            for i in range(10):
                # Use parameterized statement to prevent SQL injection
                line = f'Have a nice day {i}'
                stmt = 'INSERT INTO pythonfun (line) VALUES (%s);'
                cur.execute(stmt, (line,))

            conn.commit()
            print("Rows inserted successfully.")
        

def retrieve_row(id: int):
    """Retrieves a row from the pythonfun table by ID."""
    if id is None:
        raise ValueError("ID must be provided to retrieve a row.")
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            stmt = 'SELECT * FROM pythonfun WHERE id=%s;'
            cur.execute(stmt, (id,))

            row = cur.fetchone()

            if row is None : 
                print('Row not found')
            else:
                print('Found', row)


def trigger_retrieval_error():
    """Triggers an error by trying to retrieve a row with an invalid ID."""
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                stmt = 'SELECT line FROM pythonfun WHERE mistake=5;'
                print(stmt)
                cur.execute(stmt)
        except Exception as e:
            print(f"Error occurred: {e}")


if __name__ == "__main__":
    # Create the table
    create_table()

    # Insert sample rows
    insert_rows()

    # Retrieve a specific row by ID
    retrieve_row(id=5)

    # Insert a single row
    insert_row(line='Have a nice day 10')

    # Demostrate the retrieval error
    trigger_retrieval_error()