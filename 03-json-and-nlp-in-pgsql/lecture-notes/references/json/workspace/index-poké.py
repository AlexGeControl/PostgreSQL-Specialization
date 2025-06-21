import requests
import redis
import json
import time
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
from typing import Any, List, Dict, Optional, Iterable, Iterator
import os
import signal
import sys
import argparse
from dotenv import load_dotenv
import psycopg
from secrets import postgres_read_write, psycopg_connection_string

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class PokéAPIScraper:
    def __init__(self, root_url, max_workers, redis_host, redis_port):
        # PokéAPI configuration
        self.root_url = root_url

        # Redis configuration
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            socket_timeout=10,
            socket_connect_timeout=10,
        )

        # Threading configuration
        self.max_workers = max_workers
        self.stop_event = threading.Event()

        # Statistics
        self.stats = {
            "start_time": time.time(),
            "last_new_url_time": time.time(),
            "urls_scraped": 0,
            "urls_failed": 0,
            "errors": [],
        }
        self.stats_lock = threading.Lock()

        # Redis keys
        self.PENDING_QUEUE = "poké:pending"  # Now a sorted set instead of list
        self.COMPLETED_SET = "poké:completed"
        self.FAILED_SET = "poké:failed"
        self.DATA_PREFIX = "poké:data:"

        # URL scoring system for priority queue
        self.url_counter = 0  # For FIFO ordering within same priority

        # Request configuration
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "PokéAPI-Scraper/1.0 (Educational Purpose)"}
        )

        # Rate limiting
        self.request_delay = 0.5  # 500ms between requests
        self.max_retries = 3
        self.backoff_factor = 2

        # Timeout configuration
        self.no_new_urls_timeout = 30  # seconds

    def setup_signal_handlers(self):
        """Setup graceful shutdown on SIGINT/SIGTERM"""

        def signal_handler(signum, frame):
            logger.info("Received shutdown signal. Stopping gracefully...")
            self.stop_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _calculate_url_score(self, url: str, depth: int) -> float:
        """
        Calculate priority score for URL in sorted set queue.
        Lower scores = higher priority (processed first).

        Score Design Rationale:
        1. Resource type priority: films > people/planets/starships/vehicles/species
        2. Depth-based ordering: earlier discovered URLs get priority
        3. FIFO within same priority: monotonic counter ensures order
        4. Score range: 0-999 to allow for future priority levels

        Score Formula: (type_priority * 100) + (depth * 10) + (counter * 0.001)
        """
        # Extract resource type from URL
        url_parts = url.replace(self.root_url, "").split("/")
        resource_type = url_parts[0] if url_parts else "unknown"

        # Priority mapping: lower number = higher priority
        type_priorities = {
            "films": 1,  # Process films first (they contain many references)
            "people": 2,  # Characters are important for relationships
            "planets": 3,  # Planets have moderate references
            "starships": 4,  # Vehicles have fewer references
            "vehicles": 4,  # Same priority as starships
            "species": 5,  # Species typically have fewer outbound links
        }

        type_priority = type_priorities.get(
            resource_type, 9
        )  # Unknown types get low priority

        # Increment counter for FIFO ordering within same priority
        with self.stats_lock:
            self.url_counter += 1
            counter = self.url_counter

        # Calculate final score: type_priority * 100 + depth * 10 + counter * 0.001
        # This ensures type priority dominates, then depth, then FIFO order
        score = (type_priority * 100) + (depth * 10) + (counter * 0.001)

        return score

    def initialize_redis(self, seed_urls: Iterable[str]):
        """Initialize Redis with seed URLs and clear previous state"""
        logger.info("Initializing Redis state...")

        # Clear previous scraping session
        self.redis_client.delete(
            self.PENDING_QUEUE, self.COMPLETED_SET, self.FAILED_SET
        )

        # Clear old data (optional - comment out to preserve cache)
        for key in self.redis_client.scan_iter(match=f"{self.DATA_PREFIX}*"):
            self.redis_client.delete(key)

        # Add seed URLs to PENDING priority queue (sorted set)
        urls_added = 0
        for seed_url in seed_urls:
            initial_score = self._calculate_url_score(seed_url, 0)
            self.redis_client.zadd(self.PENDING_QUEUE, {seed_url: initial_score})
            logger.debug(f"Added seed URL: {seed_url} with score: {initial_score}")
            urls_added += 1

        logger.info(f"Added {urls_added} seed URLs to queue")

    def extract_urls_from_response(self, data: Dict) -> List[str]:
        """Extract URLs from API response"""
        urls = []

        # Define the array fields that contain URLs
        url_fields = [
            "characters",
            "films",
            "people",
            "pilots",
            "planets",
            "residents",
            "species",
            "starships",
            "vehicles",
        ]

        for field in url_fields:
            if field in data:
                if isinstance(data[field], list):
                    urls.extend(data[field])

        return [url for url in urls if url and url.startswith(self.root_url)]

    def save_response_data(self, url: str, data: Dict):
        """Save response data to Redis with structured key"""
        try:
            # Create a structured key based on URL
            key = (
                f"{self.DATA_PREFIX}{url.replace(self.root_url, '').replace('/', ':')}"
            )

            # Store as JSON string with metadata
            stored_data = {"url": url, "scraped_at": time.time(), "data": data}

            self.redis_client.set(key, json.dumps(stored_data))
            logger.debug(f"Saved data for {url}")

        except Exception as e:
            logger.error(f"Failed to save data for {url}: {e}")

    def add_new_urls(self, urls: List[str], depth: int = 1) -> int:
        """Add new URLs to pending queue, avoiding duplicates"""
        new_urls_count = 0

        for url in urls:
            # Check if URL is already completed or failed
            is_completed = self.redis_client.sismember(self.COMPLETED_SET, url)
            # Check if already in pending queue (sorted set)
            is_pending = self.redis_client.zscore(self.PENDING_QUEUE, url) is not None

            if not is_completed and not is_pending:
                # Calculate score for this URL
                score = self._calculate_url_score(url, depth)

                # Add to sorted set with calculated score
                self.redis_client.zadd(self.PENDING_QUEUE, {url: score})
                new_urls_count += 1
                logger.debug(f"Added new URL: {url} with score: {score}")

        if new_urls_count > 0:
            with self.stats_lock:
                self.stats["last_new_url_time"] = time.time()

        return new_urls_count

    def scrape_url(self, url: str) -> Optional[Dict]:
        """Scrape a single URL with retry logic and rate limiting"""
        for attempt in range(self.max_retries):
            try:
                # Rate limiting
                time.sleep(self.request_delay)

                # Make request with timeout
                response = self.session.get(url, timeout=10)
                response.raise_for_status()

                data = response.json()
                logger.info(f"Successfully scraped: {url}")

                with self.stats_lock:
                    self.stats["urls_scraped"] += 1

                return data

            except requests.exceptions.RequestException as e:
                wait_time = self.backoff_factor**attempt
                logger.warning(
                    f"Attempt {attempt + 1} failed for {url}: {e}. Waiting {wait_time}s..."
                )

                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Failed to scrape {url} after {self.max_retries} attempts"
                    )
                    with self.stats_lock:
                        self.stats["urls_failed"] += 1
                        self.stats["errors"].append(f"{url}: {str(e)}")

                    # Mark as failed in Redis
                    self.redis_client.sadd(self.FAILED_SET, url)
                    return None

            except Exception as e:
                logger.error(f"Unexpected error scraping {url}: {e}")
                with self.stats_lock:
                    self.stats["errors"].append(f"{url}: {str(e)}")
                return None

    def worker_thread(self):
        """Worker thread function"""
        logger.info(f"Worker thread started: {threading.current_thread().name}")

        while not self.stop_event.is_set():
            try:
                # Get URL from Redis PENDING priority queue (sorted set - lowest score first)
                # ZPOPMIN gets the member with the lowest score (highest priority)
                result = self.redis_client.zpopmin(self.PENDING_QUEUE, count=1)

                # If no URLs available, check if we should stop
                if not result:
                    # No URLs available, check if we should stop
                    if (
                        time.time() - self.stats["last_new_url_time"]
                        > self.no_new_urls_timeout
                    ):
                        logger.info(
                            "No new URLs found within timeout. Stopping worker."
                        )
                        self.stop_event.set()
                        break

                    # Wait a bit before checking again
                    time.sleep(1)
                    continue

                url, score = result[0]  # zpopmin returns list of tuples
                logger.debug(f"Processing URL: {url} with score: {score}")

                # Check if already processed (race condition protection)
                if self.redis_client.sismember(self.COMPLETED_SET, url):
                    continue

                # Scrape the URL
                data = self.scrape_url(url)

                if data:
                    # Save response data
                    self.save_response_data(url, data)

                    # Extract and add new URLs with increased depth
                    new_urls = self.extract_urls_from_response(data)
                    # Calculate depth from current URL's score (reverse engineer from score formula)
                    current_depth = int((score % 100) // 10)
                    new_count = self.add_new_urls(new_urls, depth=current_depth + 1)

                    if new_count > 0:
                        logger.info(f"Added {new_count} new URLs from {url}")

                    # Mark as completed
                    self.redis_client.sadd(self.COMPLETED_SET, url)

            except Exception as e:
                logger.error(f"Worker thread error: {e}")
                time.sleep(1)  # Prevent tight error loops

        logger.info(f"Worker thread finished: {threading.current_thread().name}")

    def print_statistics(self):
        """Print final scraping statistics"""
        elapsed_time = time.time() - self.stats["start_time"]

        print("\n" + "=" * 50)
        print("SCRAPING STATISTICS")
        print("=" * 50)
        print(f"Total runtime: {elapsed_time:.2f} seconds")
        print(f"URLs successfully scraped: {self.stats['urls_scraped']}")
        print(f"URLs failed: {self.stats['urls_failed']}")
        print(
            f"Average rate: {self.stats['urls_scraped'] / elapsed_time:.2f} URLs/second"
        )

        # Redis statistics
        completed_count = self.redis_client.scard(self.COMPLETED_SET)
        failed_count = self.redis_client.scard(self.FAILED_SET)
        pending_count = self.redis_client.zcard(
            self.PENDING_QUEUE
        )  # Use zcard for sorted set

        print(f"\nRedis Queue Status:")
        print(f"  Completed URLs: {completed_count}")
        print(f"  Failed URLs: {failed_count}")
        print(f"  Pending URLs: {pending_count}")

        if self.stats["errors"]:
            print(f"\nErrors encountered: {len(self.stats['errors'])}")
            for error in self.stats["errors"][-5:]:  # Show last 5 errors
                print(f"  {error}")

        print("=" * 50)

    def run(self, seed_urls: Iterable[str]):
        """Main execution method"""
        logger.info("Starting PokéAPI scraper...")

        # Setup signal handlers for graceful shutdown
        self.setup_signal_handlers()

        # Initialize Redis
        self.initialize_redis(seed_urls)

        # Start worker threads
        with ThreadPoolExecutor(
            max_workers=self.max_workers, thread_name_prefix="PokéAPIWorker"
        ) as executor:
            # Submit worker tasks
            futures = [
                executor.submit(self.worker_thread) for _ in range(self.max_workers)
            ]

            try:
                # Wait for completion or stop signal
                while not self.stop_event.is_set():
                    time.sleep(1)

                    # Check if all workers are done
                    if all(future.done() for future in futures):
                        break

                # Signal stop to all workers
                self.stop_event.set()

                # Wait for all workers to finish
                for future in as_completed(futures, timeout=30):
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Worker thread exception: {e}")

            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                self.stop_event.set()

        # Print final statistics
        self.print_statistics()

        logger.info("Scraping completed!")

    def get_scraped_data(self) -> Iterator[Dict]:
        """
        Return an iterator of all scraped JSON data from Redis.

        Yields:
            Dict: Each scraped JSON object with metadata including:
                - url: The original URL that was scraped
                - scraped_at: Timestamp when the data was scraped
                - data: The actual JSON response data from the API

        Example:
            for item in scraper.get_scraped_data():
                print(f"URL: {item['url']}")
                print(f"Title: {item['data'].get('title', 'N/A')}")
                print(f"Scraped at: {item['scraped_at']}")
        """
        try:
            # Scan for all keys with the data prefix
            for key in self.redis_client.scan_iter(match=f"{self.DATA_PREFIX}*"):
                try:
                    # Retrieve and parse the stored JSON data
                    stored_json = self.redis_client.get(key)
                    if stored_json:
                        stored_data = json.loads(stored_json)
                        yield stored_data

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON for key {key}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Error retrieving data for key {key}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scanning Redis keys: {e}")
            return


class PokéAPIPostgreSQLConnector:
    """
    PostgreSQL connector class for managing PokéAPI data ingestion.

    This class handles:
    - Database connection management
    - Table creation and schema management
    - Batch insertion of scraped PokéAPI data
    - Transaction management and error handling
    """

    def __init__(self, batch_size: int = 100):
        """
        Initialize the PostgreSQL connector.

        Args:
            batch_size: Number of records to insert before committing transaction
        """
        self.batch_size = batch_size
        self.connection_string = self._get_connection_string()

    def _get_connection_string(self) -> str:
        """
        Generates a connection string for local PostgreSQL instance using psycopg.

        Returns:
            str: A formatted connection string for psycopg.
        """
        conn_params = postgres_read_write()
        return psycopg_connection_string(conn_params)

    def get_connection(self):
        """
        Establishes a connection to the PostgreSQL database using psycopg.

        Returns:
            Connection: A psycopg connection object.
        """
        return psycopg.connect(
            self.connection_string, autocommit=False, connect_timeout=3
        )

    def create_table(self, table_name: str) -> None:
        """
        Creates the table for PokéAPI data in the PostgreSQL database.

        The table schema includes:
        - id: Auto-incrementing primary key
        - url: The original PokéAPI URL (unique constraint)
        - data: JSONB field containing the scraped data

        Args:
            table_name: Name of the table to create
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Drop existing table if it exists
                drop_stmt = f"DROP TABLE IF EXISTS {table_name} CASCADE;"
                logger.info(f"Executing: {drop_stmt}")
                cur.execute(drop_stmt)

                # Create new table with optimized schema for PokéAPI data
                create_stmt = f"""
                CREATE TABLE {table_name} (
                    id SERIAL PRIMARY KEY,
                    body JSONB NOT NULL
                );
                
                CREATE INDEX IF NOT EXISTS idx_{table_name}_body_gin ON {table_name} USING GIN (body);
                """
                logger.info(f"Executing: {create_stmt}")
                cur.execute(create_stmt)

                conn.commit()
                logger.info(f"Successfully created table: {table_name}")

    def insert_iterator_data(self, table_name: str, entities: Iterator[Dict]) -> int:
        """
        Inserts data from an iterator into the PostgreSQL database.

        Args:
            table_name: Name of the target table
            entities: Iterator of dictionaries containing url and data fields

        Returns:
            int: Number of records successfully inserted
        """
        inserted_count = 0

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    for entity in entities:
                        stmt = (
                            f"INSERT INTO {table_name} (body) VALUES (%s) RETURNING id;"
                        )
                        cur.execute(stmt, (json.dumps(entity["data"]),))
                        result = cur.fetchone()

                        if result:
                            inserted_count += 1

                        # Commit in batches
                        if inserted_count % self.batch_size == 0:
                            conn.commit()
                            logger.info(
                                f"Committed batch: {inserted_count} records inserted"
                            )

                    # Final commit
                    conn.commit()
                    logger.info(
                        f"Iterator insertion completed: {inserted_count} total records"
                    )

                except Exception as e:
                    conn.rollback()
                    logger.error(f"Error during iterator insertion: {e}")
                    raise

        return inserted_count

    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """
        Get statistics about the data in the table.

        Args:
            table_name: Name of the table to analyze

        Returns:
            Dict containing table statistics
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Get basic count
                cur.execute(f"SELECT COUNT(*) FROM {table_name};")
                total_count = cur.fetchone()[0]

                return {"total_records": total_count, "table_name": table_name}


def load_scraper_config() -> Dict[str, Any]:
    """
    Load scraper configuration from environment variables using python-dotenv.

    Returns:
        Dict containing configuration values for the scraper including:
        - redis_host: Redis server hostname
        - redis_port: Redis server port
        - max_workers: Number of worker threads
        - request_delay: Delay between requests
        - max_depth: Maximum crawling depth
    """
    # Load environment variables from .env file if it exists
    load_dotenv()

    config = {
        "max_workers": int(os.getenv("MAX_WORKERS", "8")),
        "redis_host": os.getenv("REDIS_HOST", "localhost"),
        "redis_port": int(os.getenv("REDIS_PORT", "6379")),
    }

    return config


def parse_command_line_args():
    """Parse command-line arguments for URL inputs"""
    parser = argparse.ArgumentParser(
        description="PokéAPI Web Scraper - Scrape Star Wars API data with Redis caching",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:  
  # Use default PokéAPI root URL
  python index-poké.py
        """,
    )

    parser.add_argument(
        "urls",
        nargs="*",  # Accept zero or more URLs
        help="One or more PokéAPI URLs to scrape. If none provided, defaults to the first 100 URL of PokéAPI pokemons.",
    )

    parser.add_argument(
        "--max-workers",
        type=int,
        help="Number of worker threads (overrides environment variable)",
    )

    parser.add_argument(
        "--redis-host", help="Redis server hostname (overrides environment variable)"
    )

    parser.add_argument(
        "--redis-port",
        type=int,
        help="Redis server port (overrides environment variable)",
    )

    args = parser.parse_args()

    # Default URLs if none provided
    if not args.urls:
        args.urls = [f"https://pokeapi.co/api/v2/pokemon/{id}" for id in range(1, 101)]

    return args


def main():
    """Main entry point"""
    # Load configuration from environment variables
    config = load_scraper_config()

    # Parse command-line arguments
    args = parse_command_line_args()

    # Override config with command-line arguments if provided
    if args.max_workers:
        config["max_workers"] = args.max_workers
    if args.redis_host:
        config["redis_host"] = args.redis_host
    if args.redis_port:
        config["redis_port"] = args.redis_port

    # Create scraper
    scraper = PokéAPIScraper(
        root_url="https://pokeapi.co/api/v2/pokemon/",
        max_workers=config["max_workers"],
        redis_host=config["redis_host"],
        redis_port=config["redis_port"],
    )

    # Create PostgreSQL connector
    pg_connector = PokéAPIPostgreSQLConnector(batch_size=100)

    try:
        # Run scraper
        # scraper.run(args.urls)

        # Create PostgreSQL table
        table_name = "pokeapi"
        pg_connector.create_table(table_name)

        # Insert scraped data into PostgreSQL
        pg_connector.insert_iterator_data(table_name, scraper.get_scraped_data())

        # Show table statistics
        stats = pg_connector.get_table_stats(table_name)
        print("\nPostgreSQL Table Statistics:")
        print(f"Total records: {stats['total_records']}")
        logger.info("Scraping and data insertion completed successfully!")
    except Exception as e:
        logger.error(f"Scraper failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
