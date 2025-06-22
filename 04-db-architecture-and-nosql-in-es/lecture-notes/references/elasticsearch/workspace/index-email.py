"""
Email indexing application for Elasticsearch.

This module fetches email messages from a remote mbox server and indexes them
into Elasticsearch for full-text search capabilities. It demonstrates core
Elasticsearch operations including index management and document indexing.

Prerequisites:
    Install the Elasticsearch Python client: pip install elasticsearch

Usage:
    python index-email.py

The application will prompt for the number of emails to process and then
fetch them sequentially from the mbox server, parse the content, and
index each email into Elasticsearch for full-text search.
"""

from typing import Dict, Optional, Tuple, Any
import requests
import re
from utils import datecompat
import time
import secrets

import dateutil.parser as parser  # If this import fails - just comment it out

# Elasticsearch imports - install with: pip install elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch import RequestsHttpConnection


def parse_mail_date(date_string: str) -> Optional[str]:
    """Parse a date string from an email header into ISO format.

    Args:
        date_string: Raw date string from email header (e.g., "Mon, 21 Jun 2024 10:30:00 GMT")

    Returns:
        ISO formatted date string if parsing succeeds, None otherwise.
        Falls back to datecompat.parsemaildate() if dateutil parsing fails.

    Note:
        Email date formats can vary significantly. This function attempts to parse
        using the more robust dateutil library first, then falls back to a custom
        parser for edge cases.
    """
    try:
        # Fix: Use the parameter name instead of undefined 'tdate'
        parsed_date = parser.parse(date_string)
        return parsed_date.isoformat()
    except Exception:
        # Fallback to custom date parser for problematic formats
        return datecompat.parsemaildate(date_string)


def create_elasticsearch_client() -> Elasticsearch:
    """Create and configure an Elasticsearch client connection.

    Returns:
        Configured Elasticsearch client instance ready for use.

    Note:
        This function uses the secrets.elastic() configuration to establish
        a secure connection to the Elasticsearch cluster. The connection uses
        HTTP authentication and can be configured for different schemes (http/https).
    """
    # Load Elasticsearch connection configuration from secrets
    secrets_config = secrets.elastic()

    # Create Elasticsearch client with authentication and connection settings
    # - hosts: List of Elasticsearch node addresses
    # - http_auth: Username/password tuple for HTTP basic authentication
    # - url_prefix: Optional URL prefix for hosted Elasticsearch services
    # - scheme: http or https protocol
    # - port: Elasticsearch port (usually 9200 for self-hosted, varies for cloud)
    # - connection_class: Specifies the HTTP connection implementation
    es = Elasticsearch(
        [secrets_config["host"]],
        http_auth=(secrets_config["user"], secrets_config["pass"]),
        url_prefix=secrets_config["prefix"],
        scheme=secrets_config["scheme"],
        port=secrets_config["port"],
        connection_class=RequestsHttpConnection,
    )

    return es


def initialize_elasticsearch_index(es: Elasticsearch, index_name: str) -> None:
    """Initialize Elasticsearch index by deleting existing and creating fresh.

    Args:
        es: Elasticsearch client instance
        index_name: Name of the index to initialize

    Note:
        This function performs a "fresh start" approach:
        1. Deletes existing index (ignores 400/404 errors if index doesn't exist)
        2. Creates a new empty index with default settings

        In production, you might want to:
        - Check if index exists before deleting
        - Use index templates for consistent mapping
        - Implement index versioning/aliasing strategies
    """
    # Delete existing index if it exists
    # ignore=[400, 404] means don't raise exceptions for:
    # - 400: Bad Request (index might be in invalid state)
    # - 404: Not Found (index doesn't exist)
    res = es.indices.delete(index=index_name, ignore=[400, 404])
    print("Dropped index")
    print(res)

    # Create new index with default settings
    # Elasticsearch will auto-create field mappings based on first document
    res = es.indices.create(index=index_name)
    print("Created the index...")
    print(res)


def fetch_email_content(url: str) -> Tuple[bool, str]:
    """Fetch email content from a remote URL.

    Args:
        url: URL to fetch email content from

    Returns:
        Tuple of (success: bool, content: str)
        - success: True if fetch succeeded, False otherwise
        - content: Email content if successful, error message if failed
    """
    try:
        # Make HTTP request with reasonable timeout
        response = requests.get(url, timeout=30)

        # Check for successful HTTP status
        if response.status_code != 200:
            return False, f"HTTP Error {response.status_code}"

        return True, response.text

    except KeyboardInterrupt:
        return False, "Program interrupted by user"
    except Exception as e:
        return False, f"Network error: {str(e)}"


def parse_email_structure(email_text: str) -> Tuple[bool, str, str]:
    """Parse email text into header and body sections.

    Args:
        email_text: Raw email text in mbox format

    Returns:
        Tuple of (success: bool, header: str, body: str)
        - success: True if parsing succeeded
        - header: Email header section
        - body: Email body section
    """
    # Validate that this is a proper email format (mbox starts with "From ")
    if not email_text.startswith("From "):
        return False, "", ""

    # Find the double newline that separates headers from body
    # This is the standard RFC 2822 email format separator
    separator_pos = email_text.find("\n\n")
    if separator_pos <= 0:
        return False, "", ""

    header = email_text[:separator_pos]
    body = email_text[separator_pos + 2 :]

    return True, header, body


def extract_sender_email(header: str) -> Optional[str]:
    """Extract sender email address from email header.

    Args:
        header: Email header section as string

    Returns:
        Cleaned sender email address, or None if not found

    Note:
        This function handles two common email header formats:
        1. "From: Name <email@domain.com>" - extracts email from angle brackets
        2. "From: email@domain.com" - direct email format
    """
    # Pattern 1: "From: Display Name <email@domain.com>"
    # \\S+ matches non-whitespace characters for email validation
    matches = re.findall(r"\nFrom: .* <(\S+@\S+)>\n", header)
    if len(matches) == 1:
        email = matches[0].strip().lower().replace("<", "")
        return email

    # Pattern 2: "From: email@domain.com" (no display name)
    matches = re.findall(r"\nFrom: (\S+@\S+)\n", header)
    if len(matches) == 1:
        email = matches[0].strip().lower().replace("<", "")
        return email

    return None


def extract_email_date(header: str) -> Optional[str]:
    """Extract and parse date from email header.

    Args:
        header: Email header section as string

    Returns:
        Parsed date in ISO format, or None if parsing failed

    Note:
        Email dates can be in various formats. This function:
        1. Extracts date using regex pattern matching
        2. Truncates to reasonable length to avoid parsing issues
        3. Uses the parse_mail_date function for actual parsing
    """
    # Extract date from "Date: Day, DD Mon YYYY HH:MM:SS GMT" format
    # The .* after comma handles various day name formats
    matches = re.findall(r"\nDate: .*, (.*)\n", header)
    if len(matches) != 1:
        return None

    date_string = matches[0]
    # Truncate to first 26 characters to handle overly long date strings
    date_string = date_string[:26]

    try:
        return parse_mail_date(date_string)
    except Exception:
        return None


def parse_email_headers(header: str) -> Dict[str, str]:
    """Parse email header into a dictionary of key-value pairs.

    Args:
        header: Email header section as string

    Returns:
        Dictionary mapping header names to values (all lowercase)

    Note:
        This function extracts standard email headers like:
        - Subject: Email subject line
        - To: Recipient addresses
        - CC: Carbon copy recipients
        - Content-Type: MIME type information
        - Message-ID: Unique message identifier
        etc.
    """
    header_lines = header.split("\n")
    header_dict = {}

    for line in header_lines:
        # Match "Key: Value" pattern
        # [^ :]* means any characters except space and colon (for the key)
        # .* matches any characters for the value
        matches = re.findall(r"([^ :]*): (.*)$", line)

        if len(matches) != 1:
            continue

        key_value = matches[0]
        if len(key_value) != 2:
            continue

        key = key_value[0].lower()
        value = key_value[1].lower()
        header_dict[key] = value

    return header_dict


def create_email_document(
    message_id: int,
    sender: Optional[str],
    headers: Dict[str, str],
    body: str,
    sent_date: Optional[str],
) -> Dict[str, Any]:
    """Create a document structure for Elasticsearch indexing.

    Args:
        message_id: Unique identifier for the message
        sender: Sender's email address
        headers: Dictionary of email headers
        body: Email body content
        sent_date: Parsed send date

    Returns:
        Dictionary representing the document to be indexed

    Note:
        The document structure includes:
        - offset: Unique message ID for tracking
        - sender: For email-based searches and aggregations
        - headers: All email metadata for advanced filtering
        - body: Full-text searchable content
        - date: Properly formatted date for time-based queries
    """
    # Create a copy of headers to avoid modifying the original
    doc_headers = headers.copy()
    # Override the date field with our properly parsed date
    # Handle None case by converting to string
    doc_headers["date"] = sent_date if sent_date is not None else ""

    document = {
        "offset": message_id,
        "sender": sender,
        "headers": doc_headers,
        "body": body,
    }

    return document


def index_document_to_elasticsearch(
    es: Elasticsearch, index_name: str, doc_id: str, document: Dict[str, Any]
) -> bool:
    """Index a document into Elasticsearch.

    Args:
        es: Elasticsearch client instance
        index_name: Name of the index to store the document
        doc_id: Unique identifier for the document
        document: Document data to index

    Returns:
        True if indexing succeeded, False otherwise

    Note:
        This function performs the core Elasticsearch indexing operation:
        - es.index() sends the document to Elasticsearch
        - The document is automatically analyzed for full-text search
        - If doc_id already exists, the document will be updated
        - Elasticsearch will auto-detect field types from the document structure
    """
    try:
        # Index the document into Elasticsearch
        # - index: The index name (like a database table)
        # - id: Unique document identifier (like a primary key)
        # - body: The actual document data to store and search
        response = es.index(index=index_name, id=doc_id, body=document)

        print("Added document...")
        print(response["result"])
        return True

    except Exception as e:
        print(f"Failed to index document {doc_id}: {str(e)}")
        return False


def get_user_input() -> int:
    """Get the number of messages to process from user input.

    Returns:
        Number of messages to process, or 0 if user wants to quit
    """
    user_input = input("How many messages: ")
    if len(user_input) < 1:
        return 0
    return int(user_input)


def main() -> None:
    """Main application entry point that orchestrates the email indexing process.

    This function:
    1. Sets up Elasticsearch connection and index
    2. Prompts user for number of messages to process
    3. Fetches emails from remote mbox server sequentially
    4. Parses each email and extracts metadata
    5. Indexes processed emails into Elasticsearch
    6. Handles errors gracefully with retry logic
    """
    # Initialize Elasticsearch connection
    es = create_elasticsearch_client()

    # Get index name from configuration (in test environment, uses username)
    secrets_config = secrets.elastic()
    index_name = secrets_config["user"]

    # Initialize fresh index for this session
    initialize_elasticsearch_index(es, index_name)

    # Configuration for email fetching
    base_url = "http://mbox.dr-chuck.net/sakai.devel/"

    # Tracking variables
    messages_to_process = 0
    processed_count = 0
    consecutive_failures = 0
    current_message_id = 0

    # Main processing loop
    while True:
        # Get user input for batch size
        if messages_to_process < 1:
            messages_to_process = get_user_input()
            if messages_to_process == 0:
                break

        # Process next message
        current_message_id += 1
        messages_to_process -= 1

        # Construct URL for current message
        # URL pattern: baseurl/<id>/<id+1> (mbox server convention)
        url = f"{base_url}{current_message_id}/{current_message_id + 1}"

        # Fetch email content
        success, content = fetch_email_content(url)
        if not success:
            print(f"Failed to fetch {url}: {content}")
            consecutive_failures += 1
            if consecutive_failures > 5:
                print("Too many consecutive failures, stopping...")
                break
            continue

        print(f"{url} {len(content)}")
        processed_count += 1

        # Parse email structure
        parse_success, header, body = parse_email_structure(content)
        if not parse_success:
            print("Failed to parse email structure")
            consecutive_failures += 1
            if consecutive_failures > 5:
                break
            continue

        # Extract email metadata
        sender = extract_sender_email(header)
        sent_date = extract_email_date(header)
        headers = parse_email_headers(header)

        # Create document for indexing
        document = create_email_document(
            current_message_id, sender, headers, body, sent_date
        )

        # Index document into Elasticsearch
        index_success = index_document_to_elasticsearch(
            es, index_name, str(current_message_id), document
        )

        if index_success:
            print(f"   {current_message_id}, {sender}, {sent_date}")
            # Reset failure counter on success
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            if consecutive_failures > 5:
                break

        # Rate limiting: pause every 100 documents to avoid overwhelming the server
        if processed_count % 100 == 0:
            time.sleep(1)

        # Check if we've processed the requested number of messages
        if messages_to_process <= 0:
            print(f"Done with {processed_count} messages")
            break


# Entry point
if __name__ == "__main__":
    main()
