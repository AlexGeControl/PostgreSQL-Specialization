from elasticsearch import Elasticsearch
from elasticsearch import RequestsHttpConnection
import time
import secrets
import json
import hashlib
from typing import Generator, Dict, Any, Tuple


def get_book_file_path() -> str:
    """Prompts user for book file path and validates input.

    Returns:
        str: Valid book file path

    Raises:
        Exception: If empty string is provided
    """
    bookfile = input("Enter book file (i.e. pg19337.txt): ")
    if bookfile.strip() == "":
        raise Exception("empty string detected, please try again to enter a book file")
    return bookfile


def create_elasticsearch_client() -> Tuple[Elasticsearch, str]:
    """Creates and configures Elasticsearch client using stored credentials.

    Returns:
        Tuple[Elasticsearch, str]: Configured ES client and index name
    """
    # Load authentication credentials from secrets file
    secrets_config = secrets.elastic()

    # Create Elasticsearch client with authentication and connection settings
    es = Elasticsearch(
        [secrets_config["host"]],  # Elasticsearch server hostname
        scheme=secrets_config["scheme"],  # HTTP or HTTPS protocol
        port=secrets_config[
            "port"
        ],  # Server port (usually 9200 for HTTP, 9243 for HTTPS)
        url_prefix=secrets_config["prefix"],  # URL prefix for hosted ES services
        http_auth=(
            secrets_config["user"],
            secrets_config["pass"],
        ),  # Basic auth credentials
        connection_class=RequestsHttpConnection,  # Use requests library for HTTP connections
    )

    # Use the username as the index name (common pattern for multi-tenant ES)
    indexname = secrets_config["user"]

    return es, indexname


def setup_fresh_index(es: Elasticsearch, indexname: str) -> None:
    """Deletes existing index and creates a fresh one.

    Args:
        es: Elasticsearch client instance
        indexname: Name of the index to recreate
    """
    # Delete existing index if it exists
    # ignore=[400, 404] means don't raise errors if index doesn't exist (404) or bad request (400)
    res = es.indices.delete(index=indexname, ignore=[400, 404])
    print(f"Dropped index {indexname}")
    print(res)

    # Create a new empty index
    # Elasticsearch will automatically infer field mappings when documents are added
    res = es.indices.create(index=indexname)
    print("Created the index...")
    print(res)


def parse_paragraphs_from_file(filepath: str) -> Generator[str, None, None]:
    """Parses paragraphs from a text file, yielding one paragraph at a time.

    Args:
        filepath: Path to the text file to parse

    Yields:
        str: Individual paragraphs from the file

    Note:
        Paragraphs are defined as consecutive non-empty lines separated by empty lines.
    """
    with open(filepath, "r", encoding="utf-8") as fhand:
        current_paragraph = ""

        for line in fhand:
            line = line.strip()

            # Skip empty lines when no paragraph content accumulated
            if line == "" and current_paragraph == "":
                continue

            # Empty line marks end of paragraph
            if line == "":
                if current_paragraph:
                    yield current_paragraph
                    current_paragraph = ""
                continue

            # Accumulate paragraph content
            current_paragraph = (
                current_paragraph + " " + line if current_paragraph else line
            )

        # Don't forget the last paragraph if file doesn't end with empty line
        if current_paragraph:
            yield current_paragraph


def generate_document_id(doc: Dict[str, Any]) -> str:
    """Generates a SHA256 hash to use as document ID.

    Args:
        doc: Document dictionary to hash

    Returns:
        str: SHA256 hexdigest of the document

    Note:
        Using content-based IDs ensures idempotent indexing -
        re-running with same content won't create duplicates.
    """
    # Create SHA256 hash object
    m = hashlib.sha256()

    # Convert document to JSON string and encode to bytes for hashing
    # json.dumps ensures consistent serialization regardless of dict key order
    m.update(json.dumps(doc, sort_keys=True).encode())

    return m.hexdigest()


def index_paragraph(
    es: Elasticsearch, indexname: str, paragraph: str, offset: int
) -> str:
    """Indexes a single paragraph into Elasticsearch.

    Args:
        es: Elasticsearch client instance
        indexname: Name of the target index
        paragraph: Paragraph content to index
        offset: Sequential paragraph number for ordering

    Returns:
        str: Document ID of the indexed paragraph
    """
    # Create document structure
    doc = {
        "offset": offset,  # Sequential number for paragraph ordering
        "content": paragraph,  # The actual text content to be searchable
    }

    # Generate content-based ID for idempotent indexing
    doc_id = generate_document_id(doc)

    # Index the document into Elasticsearch
    # If document with same ID exists, it will be updated (upsert behavior)
    res = es.index(
        index=indexname,  # Target index name
        id=doc_id,  # Unique document identifier
        body=doc,  # Document content to index
    )

    print(f"Added document {doc_id}\n:{res}")
    return doc_id


def index_book_paragraphs(
    es: Elasticsearch, indexname: str, filepath: str
) -> Dict[str, int]:
    """Indexes all paragraphs from a book file into Elasticsearch.

    Args:
        es: Elasticsearch client instance
        indexname: Name of the target index
        filepath: Path to the book file

    Returns:
        Dict[str, int]: Statistics about the indexing process
    """
    paragraph_count = 0
    line_count = 0
    char_count = 0

    # Process paragraphs one at a time (memory efficient for large files)
    for paragraph in parse_paragraphs_from_file(filepath):
        paragraph_count += 1

        # Count lines and characters for statistics
        line_count += paragraph.count(" ") + 1  # Approximate line count
        char_count += len(paragraph)

        # Index the paragraph
        index_paragraph(es, indexname, paragraph, paragraph_count)

        # Periodic status update and brief pause to avoid overwhelming the server
        if paragraph_count % 100 == 0:
            print(f"{paragraph_count} paragraphs loaded...")
            time.sleep(1)  # Brief pause to be gentle on the ES server

    return {
        "paragraphs": paragraph_count,
        "lines": line_count,
        "characters": char_count,
    }


def refresh_index(es: Elasticsearch, indexname: str) -> None:
    """Forces Elasticsearch to refresh the index for immediate searchability.

    Args:
        es: Elasticsearch client instance
        indexname: Name of the index to refresh

    Note:
        By default, ES refreshes indices every 1 second. This forces immediate refresh
        so newly indexed documents are immediately available for search.
    """
    res = es.indices.refresh(index=indexname)
    print(f"Index refreshed {indexname}")
    print(res)


def main() -> None:
    """Main application entry point."""
    try:
        # Get input file path from user
        book_filepath = get_book_file_path()

        # Setup Elasticsearch connection
        es, indexname = create_elasticsearch_client()

        # Create fresh index (removes any existing data)
        setup_fresh_index(es, indexname)

        # Index all paragraphs from the book
        stats = index_book_paragraphs(es, indexname, book_filepath)

        # Force index refresh for immediate searchability
        refresh_index(es, indexname)

        # Print final statistics
        print()
        print(
            f"Loaded {stats['paragraphs']} paragraphs, "
            f"{stats['lines']} lines, "
            f"{stats['characters']} characters"
        )

    except Exception as e:
        print(f"Error occurred: {e}")
        raise


if __name__ == "__main__":
    main()
