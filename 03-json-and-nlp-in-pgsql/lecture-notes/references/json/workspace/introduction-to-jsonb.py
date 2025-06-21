import argparse
import json
from pathlib import Path
import psycopg
from typing import Union
from secrets import postgres_local, psycopg_connection_string


# Get connection string to the database:
def get_connection_string():
    """Generates a connection string for PostgreSQL using psycopg.

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
    return psycopg.connect(
        conn_string,
        # this is needed to enable mogrify() method on the cursor:
        cursor_factory=psycopg.ClientCursor,
        autocommit=False,
        connect_timeout=3,
    )


def create_table():
    """Creates the JSONB tracks table in the PostgreSQL database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            stmt = "DROP TABLE IF EXISTS tracks CASCADE;"
            print(stmt)
            cur.execute(stmt)

            stmt = "CREATE TABLE IF NOT EXISTS tracks (id SERIAL, track JSONB)"
            print(stmt)
            cur.execute(stmt)

            conn.commit()
            print("JSONB tracks table created successfully.")


def insert_tracks(input_jsonpath: Union[str, Path]):
    """Inserts JSON tracks into the tracks table."""
    with open(input_jsonpath, "r") as file:
        tracks = json.load(file)

        with get_connection() as conn:
            with conn.cursor() as cur:
                # The loaded tracks is a dictionary, with keys as track IDs and values as JSON track objects
                for track_id, track_data in tracks.items():
                    track = json.dumps(track_data)
                    # Use parameterized statement to prevent SQL injection
                    stmt = "INSERT INTO tracks (track) VALUES (%s);"
                    cur.execute(stmt, (track,))

                conn.commit()
                print("Tracks inserted successfully.")


def get_stats():
    """Retrieves and prints statistics about the tracks table."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # See https://www.postgresql.org/docs/current/functions-json.html
            # for JSONB functions and operators.
            stmt = (
                "SELECT "
                "COUNT(DISTINCT(track ->> 'Track ID')) as track_count, "
                "MAX((track ->> 'Play Count')::int) as max_play_count, "
                "MIN((track ->> 'Play Count')::int) as min_play_count "
                "FROM tracks;"
            )
            cur.execute(stmt)
            track_count, max_play_count, min_play_count = cur.fetchone()
            print(
                f"Total tracks: {track_count}, Max. play count: {max_play_count}, Min. play count: {min_play_count}"
            )


def filter_tracks_by_name(name: str = "Summer Nights"):
    """Filters tracks by name and prints the results."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            for strategy, stmt in (
                (
                    "By Value",
                    (
                        "SELECT "
                        "track ->> 'Name' AS name,"
                        "track ->> 'Artist' AS artist,"
                        "track ->> 'Album' AS album "
                        "FROM tracks "
                        "WHERE track ->> 'Name' = %s;"
                    ),
                ),
                (
                    "By Sub JSONB",
                    (
                        "SELECT "
                        "track ->> 'Name' AS name,"
                        "track ->> 'Artist' AS artist,"
                        "track ->> 'Album' AS album "
                        "FROM tracks "
                        "WHERE track @> %s::jsonb;"
                    ),
                ),
            ):
                # Get the materialized query:
                parameter = name if strategy == "By Value" else f'{{"Name": "{name}"}}'
                materialized_query = cur.mogrify(stmt, (parameter,))

                # Print the materialized query:
                print(f"Query {strategy}:\n {materialized_query}\n")

                # Execute the actual query
                cur.execute(stmt, (parameter,))

                # Fetch the results
                results = cur.fetchall()
                print(f"Results:")
                for row in results:
                    print(f"  {row[0]} by {row[1]} from {row[2]}")
                print()


def filter_tracks_by_favorite_tag(play_count_threshold: int = 200):
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Create favorite tag based on play count
            stmt = (
                "UPDATE tracks "
                "SET track = jsonb_set(track, '{Favorite}', 'true') "
                "WHERE (track ->> 'Play Count')::int > %s;"
            )
            cur.execute(stmt, (play_count_threshold,))

            # Check results:
            stmt = (
                "SELECT "
                "COUNT(DISTINCT(track ->> 'Track ID')) as favorite_track_count "
                "FROM tracks "
                "WHERE track ? 'Favorite';"
            )
            cur.execute(stmt)
            (favorite_track_count,) = cur.fetchone()
            print(
                f"Total favorite tracks (by Play Count > {play_count_threshold}): {favorite_track_count}"
            )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Introduction to JSONB using tracks table in PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data/itunes-library/tracks.json

This will create a JSONB table named 'tracks' in the PostgreSQL database and insert the tracks from the specified JSON file.:
        """,
    )

    parser.add_argument(
        "input_jsonpath",
        type=str,
        help="Path to the iTunes library tracks JSON file to ingest into the database",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed statistics after conversion",
    )

    args = parser.parse_args()

    return args


def main() -> None:
    """
    Main function that handles command-line arguments and manages the JSONB tracks table.
    """
    args = parse_args()

    # Validate input file
    input_jsonpath = Path(args.input_jsonpath)
    if not input_jsonpath.exists():
        print(f"Error: Input JSON file not found: {input_jsonpath}")
        return

    if not input_jsonpath.is_file():
        print(f"Error: Input path is not a file: {input_jsonpath}")
        return

    # Convert the library
    try:
        # Create the table
        create_table()

        # Insert sample rows
        insert_tracks(args.input_jsonpath)

        # Show tracks statistics
        get_stats()

        # Query tracks by name
        filter_tracks_by_name()

        # Filter tracks by favorite tag based on play count
        filter_tracks_by_favorite_tag()

        # Print statistics if verbose mode is enabled
        if args.verbose:
            pass

        print(f"\nWelcome to the world of JSONB in PostgreSQL!\n")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error: Unexpected error occurred - {e}")


if __name__ == "__main__":
    main()
