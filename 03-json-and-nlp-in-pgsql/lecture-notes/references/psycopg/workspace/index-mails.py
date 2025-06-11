import psycopg
from secrets import (
    postgres_local,
    psycopg_connection_string
)
import re
import requests
from time import sleep
from tqdm import tqdm
from typing import Generator, Optional, Tuple

from utils import parse_mail_date


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


def create_table(table_name: str):
    """Creates the table for mails in the PostgreSQL database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            stmt = f'DROP TABLE IF EXISTS {table_name} CASCADE;'
            print(stmt)
            cur.execute(stmt)

            stmt = (
                f'CREATE TABLE {table_name} '
                 '(id SERIAL, email TEXT, sent_at TIMESTAMPTZ, subject TEXT, header TEXT, body TEXT);'
            )
            print(stmt)
            cur.execute(stmt)

            conn.commit()
            print(f'Table for mails {table_name} created successfully.')


def get_mail_url(mail_id: int, base_url: str = 'http://mbox.dr-chuck.net/sakai.devel') -> str:
    """Generate URL for fetching mail by ID.
    
    Args:
        mail_id: The ID of the mail to fetch
        base_url: Base URL for the mail service
        
    Returns:
        str: Complete URL for the mail
    """
    return f"{base_url}/{mail_id}/{mail_id + 1}"


def fetch_mail_content(url: str) -> Optional[str]:
    """Fetch mail content from the given URL.
    
    Args:
        url: The URL to fetch mail content from
        
    Returns:
        Optional[str]: The mail content if successful, None otherwise
    """
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print('Error code=', response.status_code, url)
            return None
        return response.text
    except KeyboardInterrupt:
        print('')
        print('Program interrupted by user...')
        raise  # Re-raise to maintain program flow
    except Exception as e:
        print('Unable to retrieve or parse page', url)
        print('Error', e)
        return None


def parse_mail_content(mail_content: str) -> tuple[Optional[str], Optional[str]]:
    """Parse mail content into header and body sections.
    
    Args:
        mail_content: Raw mail content string
        
    Returns:
        tuple[Optional[str], Optional[str]]: A tuple containing (header, body) if parsing
        is successful, (None, None) otherwise
    """
    if mail_content.startswith('From '):
        delimiter_position = mail_content.find('\n\n')
        if delimiter_position > 0:
            header = mail_content[:delimiter_position]
            body = mail_content[delimiter_position+2:]
            return (header, body)
        
    return (None, None)


def extract_email_from_header(header: str) -> Optional[str]:
    """Extract email address from mail header.
    
    Args:
        header: The mail header string
        
    Returns:
        Optional[str]: The extracted email address if found, None otherwise
    """
    # Single regex with non-capturing group 
    # to match both formats: "From: Name <email@domain>" and "From: email@domain"
    matches = re.findall(r'\nFrom: (?:.*<)?(\S+@\S+)>?\n', header)
    if matches:
        email = matches[0].strip().lower().replace('<', '')
        return email
    return None


def extract_subject_from_header(header: str) -> Optional[str]:
    """Extract subject from mail header.
    
    Args:
        header: The mail header string
        
    Returns:
        Optional[str]: The extracted subject if found, None otherwise
    """
    matches = re.findall(r'\nSubject: (.*)\n', header)
    if matches:
        return matches[0].strip().lower()
    return None


def extract_date_from_header(header: str) -> Optional[str]:
    """Extract and parse date from mail header.
    
    Args:
        header: The mail header string
        
    Returns:
        Optional[str]: The parsed date if found and valid, None otherwise
    """
    matches = re.findall(r'\nDate: .*, (.*)\n', header)
    if matches:
        mail_date = matches[0][:26]
        try:
            sent_at = parse_mail_date(mail_date)
            return sent_at
        except:
            print('Unable to parse date', mail_date)
            return None
    return None

def extract_mail_metadata(header: str) -> Optional[tuple[str, str, str]]:
    """Extract email metadata from mail header.
    
    Args:
        header: The mail header string
        
    Returns:
        Optional[tuple[str, str, str]]: A tuple containing (email, sent_at, subject) if all
        metadata is successfully extracted, None otherwise
    """
    email = extract_email_from_header(header)
    sent_at = extract_date_from_header(header)
    subject = extract_subject_from_header(header)

    if email and sent_at and subject:
        return (email, sent_at, subject)
    
    return None


def parse_mails(n: int) -> Generator[Tuple[str, str, str, str, str], None, None]:
    """Parse mails from a sequence of IDs."""
    for mail_id in range(1, n + 1):
        url = get_mail_url(mail_id)
        print(f'Fetching mail from {url}')
        
        mail_content = fetch_mail_content(url)
        if not mail_content:
            continue

        header, body = parse_mail_content(mail_content)
        if not header or not body:
            print(f'Failed to parse mail content for ID {mail_id}')
            continue

        mail_metadata = extract_mail_metadata(header)
        if not mail_metadata:
            print(f'Failed to extract complete metadata for mail ID {mail_id}')
            continue
        email, sent_at, subject = mail_metadata

        yield (email, sent_at, subject, header, body)


def insert_mails_into_table(table_name: str, mails: Generator[Tuple[str, str, str, str, str], None, None]):
    """Inserts paragraphs into the book table in the PostgreSQL database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            for mail in tqdm(
                mails, 
                desc=f'Inserting mails into table',
                unit=' mail'
            ):
                email, sent_at, subject, header, body = mail
                stmt = (
                    f"INSERT INTO {table_name} (email, sent_at, subject, header, body) "
                    "VALUES (%s, %s, %s, %s, %s) RETURNING id;"
                )
                cur.execute(stmt, (email, sent_at, subject, header, body))
                (id, ) = cur.fetchone()

                if id % 100 == 0:
                    conn.commit()

            print(f'Inserted {id + 1} mails into table successfully.')


def index_mails(table_name: str):
    """Creates an inverted index for the mail body in the PostgreSQL database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            stmt = f"CREATE INDEX IF NOT EXISTS idx_{table_name}_body ON {table_name} USING gin(to_tsvector('english', body));"
            print(stmt)
            cur.execute(stmt)
            conn.commit()
            sleep(5)
            print(f'Inverted index for {table_name} created successfully.')


def search_mail_by_keywords(table_name: str, search_term: str) -> str:
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
            stmt = f"""
                SELECT 
                    email, subject,
                    ts_rank(to_tsvector('english', body), to_tsquery('english', %s)) as ts_rank
                FROM mails
                WHERE to_tsquery('english', %s) @@ to_tsvector('english', body)
                ORDER BY ts_rank DESC;
            """
            cur.execute(stmt, (search_term, search_term))
            
            # Fetch all rows from the query plan
            result = "\n".join(
                f"Rank: {rank}, Sender: {email}, Subject: {subject}" 
                for (rank, (email, subject, _)) in enumerate(cur.fetchall(), start=1)
            )

            return result


if __name__ == '__main__':
    # Set the table name for mails
    table_name='mails'

    # Create the table for mails
    create_table(table_name=table_name)

    # Parse mails and insert them into the table
    insert_mails_into_table(table_name=table_name, mails=parse_mails(100))

    # Index mail:
    index_mails(table_name=table_name)  

    # Query by key words:
    print(
        search_mail_by_keywords(table_name=table_name, search_term='personal & learning')
    )      