#!/usr/bin/env python3
"""
CLI tool to interrogate ChromaDB vector stores.

Provides easy access to inspect collections, query embeddings, and view metadata.
"""

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import chromadb
    from chromadb.config import Settings

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


def list_collections(db_path: Path) -> None:
    """List all collections in the ChromaDB."""
    if not CHROMA_AVAILABLE:
        print("ChromaDB not available. Install with: uv pip install chromadb")
        return

    try:
        settings = Settings(
            persist_directory=str(db_path),
            is_persistent=True,
            anonymized_telemetry=False,
        )
        client = chromadb.Client(settings)
        collections = client.list_collections()

        print(f"Collections in {db_path}:")
        if not collections:
            print("  No collections found")
        else:
            for collection in collections:
                count = collection.count()
                print(f"  - {collection.name} ({count} items)")
                print(f"    ID: {collection.id}")
                if collection.metadata:
                    print(f"    Metadata: {collection.metadata}")
    except Exception as e:
        print(f"Error listing collections: {e}")


def query_collection(
    db_path: Path,
    collection_name: str = "conversation",
    query_text: str = "",
    n_results: int = 5,
) -> None:
    """Query a specific collection."""
    if not CHROMA_AVAILABLE:
        print("ChromaDB not available. Install with: uv pip install chromadb")
        return

    try:
        settings = Settings(
            persist_directory=str(db_path),
            is_persistent=True,
            anonymized_telemetry=False,
        )
        client = chromadb.Client(settings)
        collection = client.get_collection(collection_name)

        if query_text:
            # Query with text
            results = collection.query(query_texts=[query_text], n_results=n_results)
            print(f"Query results for '{query_text}':")
        else:
            # Get all items (limited)
            results = collection.get(limit=n_results)
            print(f"First {n_results} items in collection '{collection_name}':")

        # Display results
        if "ids" in results:
            ids = (
                results["ids"][0]
                if isinstance(results["ids"][0], list)
                else results["ids"]
            )
            documents = results.get("documents", [None] * len(ids))
            if documents and isinstance(documents[0], list):
                documents = documents[0]
            metadatas = results.get("metadatas", [None] * len(ids))
            if metadatas and isinstance(metadatas[0], list):
                metadatas = metadatas[0]
            distances = results.get("distances", [None] * len(ids))
            if distances and isinstance(distances[0], list):
                distances = distances[0]

            for i, item_id in enumerate(ids):
                print(f"\n  Item {i+1}:")
                print(f"    ID: {item_id}")
                if distances and distances[i] is not None:
                    print(f"    Distance: {distances[i]:.4f}")
                if documents and documents[i]:
                    doc_preview = (
                        documents[i][:200] + "..."
                        if len(documents[i]) > 200
                        else documents[i]
                    )
                    print(f"    Document: {doc_preview}")
                if metadatas and metadatas[i]:
                    print(f"    Metadata: {json.dumps(metadatas[i], indent=6)}")
        else:
            print("  No results found")

    except Exception as e:
        print(f"Error querying collection: {e}")


def inspect_sqlite(db_path: Path) -> None:
    """Inspect the underlying SQLite database."""
    sqlite_path = db_path / "chroma.sqlite3"
    if not sqlite_path.exists():
        print(f"SQLite database not found at {sqlite_path}")
        return

    try:
        conn = sqlite3.connect(str(sqlite_path))
        cursor = conn.cursor()

        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        print(f"SQLite tables in {sqlite_path}:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} rows")

            # Show sample data for key tables
            if table in ["collections", "embeddings", "embedding_metadata"]:
                cursor.execute(f"SELECT * FROM {table} LIMIT 2")
                rows = cursor.fetchall()
                if rows:
                    # Get column names
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in cursor.fetchall()]
                    print(f"    Columns: {', '.join(columns)}")
                    print(f"    Sample: {rows[0] if rows else 'No data'}")

        conn.close()

    except Exception as e:
        print(f"Error inspecting SQLite database: {e}")


def show_stats(db_path: Path) -> None:
    """Show statistics about the vector store."""
    print(f"Vector Store Statistics for {db_path}:")
    print("=" * 50)

    # Check metadata.json if it exists
    metadata_file = db_path / "metadata.json"
    if metadata_file.exists():
        try:
            with open(metadata_file) as f:
                metadata = json.load(f)
            print(f"Metadata.json: {len(metadata)} exchanges")

            # Analyze timestamps
            if metadata:
                timestamps = [ex.get("timestamp", 0) for ex in metadata.values()]
                earliest = min(timestamps)
                latest = max(timestamps)
                import datetime

                earliest_date = datetime.datetime.fromtimestamp(earliest).strftime(
                    "%Y-%m-%d %H:%M"
                )
                latest_date = datetime.datetime.fromtimestamp(latest).strftime(
                    "%Y-%m-%d %H:%M"
                )
                print(f"Time range: {earliest_date} to {latest_date}")

        except Exception as e:
            print(f"Error reading metadata.json: {e}")

    # ChromaDB stats
    if CHROMA_AVAILABLE:
        list_collections(db_path)
    else:
        print("ChromaDB not available for collection stats")

    print()
    # SQLite stats
    inspect_sqlite(db_path)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="ChromaDB CLI interrogation tool")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to ChromaDB directory (default: current directory)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List collections
    list_parser = subparsers.add_parser("list", help="List all collections")

    # Query collection
    query_parser = subparsers.add_parser("query", help="Query a collection")
    query_parser.add_argument(
        "--collection",
        "-c",
        default="conversation",
        help="Collection name (default: conversation)",
    )
    query_parser.add_argument(
        "--text", "-t", default="", help="Query text (if empty, shows first N items)"
    )
    query_parser.add_argument(
        "--limit", "-n", type=int, default=5, help="Number of results (default: 5)"
    )

    # Inspect SQLite
    sqlite_parser = subparsers.add_parser("sqlite", help="Inspect SQLite database")

    # Show stats
    stats_parser = subparsers.add_parser("stats", help="Show vector store statistics")

    args = parser.parse_args()

    db_path = Path(args.path)
    if not db_path.exists():
        print(f"Error: Path does not exist: {db_path}")
        return 1

    if not db_path.is_dir():
        print(f"Error: Path is not a directory: {db_path}")
        return 1

    # Default to stats if no command specified
    command = args.command or "stats"

    if command == "list":
        list_collections(db_path)
    elif command == "query":
        query_collection(db_path, args.collection, args.text, args.limit)
    elif command == "sqlite":
        inspect_sqlite(db_path)
    elif command == "stats":
        show_stats(db_path)
    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    exit(main())
