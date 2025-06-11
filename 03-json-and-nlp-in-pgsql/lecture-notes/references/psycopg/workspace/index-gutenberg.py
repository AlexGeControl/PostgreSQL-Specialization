import argparse
import os
import psycopg
from secrets import (
    postgres_local,
    psycopg_connection_string
)
from time import sleep
from tqdm import tqdm
from typing import Generator


def get_connection_string():
    """Generates a connection string for local PostgreSQL instance using psycopg.
    
    Returns:
        str: A formatted connection string for psycopg.
    """
    conn_params = postgres_local()
    return psycopg_connection_string(conn_params)


def get_connection():
    """Establishes a connection to the PostgreSQL database using psycopg.
    
    Returns:
        Connection: A psycopg connection object.
    """
    conn_string = get_connection_string()
    return psycopg.connect(conn_string, autocommit=False, connect_timeout=3)


def get_book_name_from_filepath(book_filepath: str) -> str:
    """Extract book name from file path by removing directory and extension.
    
    Args:
        book_filepath (str): Full path to the book file
        
    Returns:
        str: Base name of the file without extension
    """
    # Get the base filename without directory path
    filename = os.path.basename(book_filepath)
    # Remove the file extension
    (book_name, _) = os.path.splitext(filename)
    return book_name


def create_book_table(book_name: str):
    """Creates the table for book in the PostgreSQL database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            stmt = f'DROP TABLE IF EXISTS {book_name} CASCADE;'
            print(stmt)
            cur.execute(stmt)

            stmt = f'CREATE TABLE {book_name} (id SERIAL, paragraph TEXT);'
            print(stmt)
            cur.execute(stmt)

            conn.commit()
            print(f'Table for book {book_name} created successfully.')


def parse_paragraphs_from_book(book_filepath: str) -> Generator[str, None, None]:
    """Parses paragraphs from a book file into a generator of strings."""
    paragraph = []
    with open(book_filepath, 'r', encoding='utf-8') as file:
        # Leverage Python's memory-efficient file iterator
        for line in file:  
            line = line.rstrip('\n')
            
            if line.strip() == '':
                if paragraph:
                    # Only one paragraph worth of data in memory
                    yield '\n'.join(paragraph)
                    # Clear for next paragraph
                    paragraph = []  
            else:
                paragraph.append(line)
    
    if paragraph:
        return '\n'.join(paragraph)


def insert_paragraphs_into_book_table(book_name: str, paragraphs: Generator[str, None, None]):
    """Inserts paragraphs into the book table in the PostgreSQL database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            for paragraph in tqdm(
                paragraphs, 
                desc=f'Inserting paragraphs into {book_name} table',
                unit='paragraph'
            ):
                stmt = f"INSERT INTO {book_name} (paragraph) VALUES (%s) RETURNING id;"
                cur.execute(stmt, (paragraph,))
                (id, ) = cur.fetchone()

                if id % 100 == 0:
                    conn.commit()

            print(f'Inserted {id + 1} paragraphs into table successfully.')


def index_book_paragraphs(book_name: str):
    """Creates an inverted index for the book paragraphs in the PostgreSQL database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            stmt = f"CREATE INDEX IF NOT EXISTS idx_{book_name}_paragraph ON {book_name} USING gin(to_tsvector('english', paragraph));"
            print(stmt)
            cur.execute(stmt)
            conn.commit()
            sleep(5)
            print(f'Inverted index for {book_name} created successfully.')


def get_query_plan_for_paragraph_search(book_name: str, search_term: str) -> str:
    """
    Returns the query execution plan for a full-text paragraph search query.
    
    Args:
        book_name (str): Name of the book table to search
        search_term (str): Term to search for in the paragraphs
        
    Returns:
        str: Formatted query execution plan
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Execute EXPLAIN for the full-text search query
            explain_stmt = f"""
                EXPLAIN (
                    SELECT 
                        COUNT(*) AS hit_count
                    FROM {book_name} 
                    WHERE to_tsquery('english', %s) @@ to_tsvector('english', paragraph)
                );
            """
            cur.execute(explain_stmt, (search_term,))
            
            # Fetch all rows from the query plan
            plan ="\n".join(plan_line for (plan_line, ) in cur.fetchall())
            
            return plan
        

def parse_arguments():
    """Parses command line arguments for Project Gutenberg book file path."""

    parser = argparse.ArgumentParser(
        description='Insert Project Gutenberg book into a PostgreSQL table.'
    )

    parser.add_argument('book_filepath', type=str, help='Path to the book file')
    
    return parser.parse_args()


if __name__ == "__main__":
    # Parse book file path:
    book_filepath = parse_arguments().book_filepath

    # Parse book name from file path:
    book_name = get_book_name_from_filepath(book_filepath)

    # Create the book table
    create_book_table(book_name=book_name)

    # Insert paragraphs into the book table
    insert_paragraphs_into_book_table(
        book_name=book_name, 
        paragraphs=parse_paragraphs_from_book(book_filepath)
    )

    # Create inverted index for the book paragraphs
    index_book_paragraphs(book_name=book_name)

    # Show query plan for searching paragraphs:
    search_term='love'
    print(
        f"Sample query plan for searching paragraphs using key word {search_term} in the book '{book_name}':\n"
        f"{get_query_plan_for_paragraph_search(book_name=book_name, search_term='love')}"
    )