"""
Tweet indexing and search demonstration for Elasticsearch.

This module demonstrates basic Elasticsearch operations including:
- Index management (create/delete)
- Document indexing
- Document retrieval
- Full-text search with boolean queries
- Index refresh operations

Prerequisites:
    Install the Elasticsearch Python client: pip install 'elasticsearch<7.14.0'

Usage:
    python index-tweet.py

The application will create a fresh index, add a sample tweet document,
and demonstrate various search operations.

References:
    - https://www.pg4e.com/code/elastictweet.py
    - https://elasticsearch-py.readthedocs.io/en/master/
"""

from datetime import datetime
from typing import Dict, Any, List
from elasticsearch import Elasticsearch
from elasticsearch import RequestsHttpConnection

import secrets


def create_elasticsearch_client() -> Elasticsearch:
    """Create and configure an Elasticsearch client connection.

    Returns:
        Configured Elasticsearch client instance for tweet operations.

    Note:
        This function loads connection settings from the secrets module and
        creates an authenticated connection to the Elasticsearch cluster.
        The connection uses HTTP basic authentication and can work with both
        local and cloud-hosted Elasticsearch instances.
    """
    # Load Elasticsearch connection configuration from secrets
    secrets_config = secrets.elastic()

    # Create Elasticsearch client with authentication and connection settings
    # The Elasticsearch() constructor accepts multiple configuration options:
    # - hosts: List of Elasticsearch node URLs
    # - http_auth: Tuple of (username, password) for HTTP basic auth
    # - url_prefix: API endpoint prefix (useful for hosted services)
    # - scheme: 'http' or 'https' protocol
    # - port: Port number (typically 9200 for local, varies for cloud)
    # - connection_class: HTTP client implementation to use
    es = Elasticsearch(
        [secrets_config["host"]],
        http_auth=(secrets_config["user"], secrets_config["pass"]),
        url_prefix=secrets_config["prefix"],
        scheme=secrets_config["scheme"],
        port=secrets_config["port"],
        connection_class=RequestsHttpConnection,
    )

    return es


def initialize_fresh_index(es: Elasticsearch, index_name: str) -> None:
    """Initialize a fresh Elasticsearch index by deleting and recreating it.

    Args:
        es: Elasticsearch client instance
        index_name: Name of the index to initialize

    Note:
        This function performs a "clean slate" operation:
        1. Deletes any existing index with the same name
        2. Creates a new empty index with default settings

        The ignore=[400, 404] parameter tells Elasticsearch to ignore:
        - 400: Bad Request errors (if index is corrupted)
        - 404: Not Found errors (if index doesn't exist)

        This is useful for development/testing but should be used
        carefully in production environments.
    """
    # Delete existing index if it exists
    # Reference: https://elasticsearch-py.readthedocs.io/en/master/api.html#indices
    res = es.indices.delete(index=index_name, ignore=[400, 404])
    print("Dropped index")
    print(res)

    # Create new empty index with default settings
    # Elasticsearch will automatically create field mappings when documents are indexed
    res = es.indices.create(index=index_name)
    print("Created the index...")
    print(res)


def create_sample_tweet_document() -> Dict[str, Any]:
    """Create a sample tweet document for indexing.

    Returns:
        Dictionary representing a tweet document with metadata.

    Note:
        The document structure includes:
        - author: Username of the tweet author
        - type: Document type for filtering (useful in multi-type indices)
        - text: The tweet content for full-text search
        - timestamp: When the tweet was created (for time-based queries)

        Important: Once you start indexing documents, you cannot change
        the data type of existing fields without reindexing.
    """
    document = {
        "author": "kimchy",
        "type": "tweet",
        "text": (
            "even when there is no power to the computer Examples of secondary"
            "memory are disk drives or flash memory typically found in USB"
            "sticks and portable music players"
            "keyboard mouse microphone speaker touchpad etc They are all of"
            "the ways we interact with the computer"
        ),
        "timestamp": datetime.now(),
    }

    return document


def index_document(
    es: Elasticsearch, index_name: str, doc_id: str, document: Dict[str, Any]
) -> Dict[str, Any]:
    """Index a document into Elasticsearch.

    Args:
        es: Elasticsearch client instance
        index_name: Name of the index to store the document
        doc_id: Unique identifier for the document
        document: Document data to index

    Returns:
        Elasticsearch response containing indexing result information.

    Note:
        The es.index() operation:
        - Stores the document in the specified index
        - Assigns the given document ID (or auto-generates if not provided)
        - Automatically analyzes text fields for full-text search
        - Returns metadata about the indexing operation

        If a document with the same ID already exists, it will be updated.
        The 'result' field in the response indicates whether the document
        was 'created' or 'updated'.
    """
    # Index the document into Elasticsearch
    # The document is automatically analyzed and made searchable
    res = es.index(index=index_name, id=doc_id, body=document)
    print("Added document...")
    print(res["result"])

    return res


def retrieve_document(
    es: Elasticsearch, index_name: str, doc_id: str
) -> Dict[str, Any]:
    """Retrieve a document from Elasticsearch by ID.

    Args:
        es: Elasticsearch client instance
        index_name: Name of the index containing the document
        doc_id: Unique identifier of the document to retrieve

    Returns:
        Elasticsearch response containing the document and metadata.

    Note:
        The es.get() operation:
        - Retrieves a document by its exact ID
        - Returns the document source plus metadata
        - Is very fast as it's a direct lookup (not a search)
        - Will raise an exception if the document doesn't exist

        The response includes:
        - _source: The original document content
        - _index, _type, _id: Document location metadata
        - _version: Document version number (increments on updates)
    """
    # Retrieve document by ID - this is a direct lookup, not a search
    res = es.get(index=index_name, id=doc_id)
    print("Retrieved document...")
    print(res)

    return res


def refresh_index(es: Elasticsearch, index_name: str) -> Dict[str, Any]:
    """Refresh an Elasticsearch index to make recent changes searchable.

    Args:
        es: Elasticsearch client instance
        index_name: Name of the index to refresh

    Returns:
        Elasticsearch response confirming the refresh operation.

    Note:
        By default, Elasticsearch refreshes indices every 1 second, making
        new documents searchable. The refresh operation forces an immediate
        refresh, which is useful for:
        - Demo purposes (immediate search results)
        - Testing scenarios
        - Time-sensitive applications

        Warning: Frequent manual refreshes can impact performance in
        production systems. Use sparingly and consider the refresh_interval
        setting for better control.

        Reference: https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-refresh.html
    """
    # Force index refresh to make recent changes immediately searchable
    # Normally Elasticsearch refreshes automatically every ~1 second
    res = es.indices.refresh(index=index_name)
    print("Index refreshed")
    print(res)

    return res


def create_search_query(search_term: str, document_type: str) -> Dict[str, Any]:
    """Create a boolean search query for Elasticsearch.

    Args:
        search_term: Text to search for in document content
        document_type: Document type to filter by

    Returns:
        Elasticsearch query DSL as a dictionary.

    Note:
        This function demonstrates a boolean query with:
        - must clause: Documents MUST match this condition (affects scoring)
        - filter clause: Documents must match but doesn't affect scoring

        Query vs Filter context:
        - Query context: "How well does this document match?" (affects _score)
        - Filter context: "Does this document match?" (yes/no, cached)

        The match query performs full-text search with analysis:
        - Tokenizes the search term
        - Applies the same analysis as when indexing
        - Finds documents containing the terms

        Reference: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-filter-context.html
    """
    query = {
        "query": {
            "bool": {
                # must: Query context - affects document scoring
                "must": {
                    "match": {
                        "text": search_term  # Full-text search in the 'text' field
                    }
                },
                # filter: Filter context - fast, cacheable, no scoring
                "filter": {
                    "match": {"type": document_type}  # Exact match for document type
                },
            }
        }
    }

    return query


def search_documents(
    es: Elasticsearch, index_name: str, query: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute a search query against an Elasticsearch index.

    Args:
        es: Elasticsearch client instance
        index_name: Name of the index to search
        query: Elasticsearch query DSL dictionary

    Returns:
        Search results including matching documents and metadata.

    Note:
        The es.search() operation:
        - Executes the provided query against the index
        - Returns matching documents with relevance scores
        - Includes metadata about the search (total hits, max score, etc.)

        Search results structure:
        - hits.total: Total number of matching documents
        - hits.hits: Array of matching documents
        - hits.max_score: Highest relevance score
        - Each hit contains: _source (document), _score (relevance), _id, etc.
    """
    # Execute the search query
    res = es.search(index=index_name, body=query)
    print("Search results...")
    print(res)

    return res


def display_search_results(search_results: Dict[str, Any]) -> None:
    """Display search results in a user-friendly format.

    Args:
        search_results: Elasticsearch search response dictionary

    Note:
        This function demonstrates how to extract and display information
        from Elasticsearch search results:
        - hits.hits contains the array of matching documents
        - Each hit has a _source field with the original document
        - Additional metadata like _score (relevance) is also available
    """
    hits = search_results["hits"]["hits"]
    print()
    print("Got %d Hits:" % len(hits))

    # Iterate through search results and display formatted output
    for hit in hits:
        source = hit["_source"]  # Extract the original document
        print(f"{source['timestamp']} {source['author']}: {source['text']}")


def main() -> None:
    """Main application entry point that demonstrates Elasticsearch operations.

    This function orchestrates a complete Elasticsearch workflow:
    1. Connect to Elasticsearch cluster
    2. Initialize a fresh index
    3. Create and index a sample document
    4. Retrieve the document by ID
    5. Refresh the index for immediate searchability
    6. Perform a full-text search with filtering
    7. Display the search results
    """
    # Initialize Elasticsearch connection
    es = create_elasticsearch_client()

    # Get index name from configuration (uses username in test environment)
    secrets_config = secrets.elastic()
    index_name = secrets_config["user"]

    # Create a fresh index (delete existing and create new)
    initialize_fresh_index(es, index_name)

    # Create sample tweet document
    tweet_doc = create_sample_tweet_document()

    # Index the document with a specific ID
    index_document(es, index_name, "abc", tweet_doc)

    # Retrieve the document by ID to verify it was stored
    retrieve_document(es, index_name, "abc")

    # Refresh index to make the document immediately searchable
    refresh_index(es, index_name)

    # Create a search query looking for "microphone" in tweet documents
    search_query = create_search_query("microphone", "tweet")

    # Execute the search
    results = search_documents(es, index_name, search_query)

    # Display results in a readable format
    display_search_results(results)


# Entry point
if __name__ == "__main__":
    main()
