#!/usr/bin/env python3
"""
Script to migrate vector store data from Eris to Ada.

This script copies all exchanges from the source vector store (Eris)
to the destination vector store (Ada), preserving all metadata and embeddings.
"""

import json
import shutil
import sqlite3
import argparse
from pathlib import Path
from typing import Dict, Any


def migrate_metadata(source_path: Path, dest_path: Path) -> None:
    """
    Migrate metadata.json from source to destination.

    Parameters
    ----------
    source_path : Path
        Path to source vector store directory
    dest_path : Path
        Path to destination vector store directory
    """
    source_metadata = source_path / "metadata.json"
    dest_metadata = dest_path / "metadata.json"

    # Load source metadata
    with open(source_metadata, "r") as f:
        source_data = json.load(f)

    # Load existing destination metadata if it exists
    dest_data = {}
    if dest_metadata.exists():
        with open(dest_metadata, "r") as f:
            dest_data = json.load(f)

    # Merge source data into destination (source takes precedence on conflicts)
    merged_count = 0
    for exchange_id, exchange_data in source_data.items():
        if exchange_id not in dest_data:
            dest_data[exchange_id] = exchange_data
            merged_count += 1

    # Save merged metadata
    with open(dest_metadata, "w") as f:
        json.dump(dest_data, f, indent=2)

    print(f"Merged {merged_count} new exchanges into metadata.json")
    print(f"Total exchanges in destination: {len(dest_data)}")


def migrate_chroma_db(source_path: Path, dest_path: Path) -> None:
    """
    Migrate ChromaDB SQLite database from source to destination.

    Parameters
    ----------
    source_path : Path
        Path to source vector store directory
    dest_path : Path
        Path to destination vector store directory
    """
    source_db = source_path / "chroma.sqlite3"
    dest_db = dest_path / "chroma.sqlite3"

    if not source_db.exists():
        print(f"Warning: Source ChromaDB not found at {source_db}")
        return

    # Connect to both databases
    source_conn = sqlite3.connect(str(source_db))
    dest_conn = sqlite3.connect(str(dest_db))

    try:
        # Get all table names from source
        source_cursor = source_conn.cursor()
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in source_cursor.fetchall()]

        migrated_records = 0

        for table in tables:
            print(f"Processing table: {table}")

            # Get source table data
            source_cursor.execute(f"SELECT * FROM {table}")
            source_rows = source_cursor.fetchall()

            # Get column info
            source_cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in source_cursor.fetchall()]

            if not source_rows:
                continue

            # Create placeholders for INSERT
            placeholders = ",".join(["?" for _ in columns])
            column_names = ",".join(columns)

            # Insert data into destination (using INSERT OR IGNORE to skip duplicates)
            dest_cursor = dest_conn.cursor()
            insert_query = f"INSERT OR IGNORE INTO {table} ({column_names}) VALUES ({placeholders})"

            for row in source_rows:
                try:
                    dest_cursor.execute(insert_query, row)
                    migrated_records += 1
                except sqlite3.Error as e:
                    print(f"Warning: Failed to insert row in {table}: {e}")

        dest_conn.commit()
        print(f"Migrated {migrated_records} records from ChromaDB")

    except sqlite3.Error as e:
        print(f"Error during ChromaDB migration: {e}")
        dest_conn.rollback()
    finally:
        source_conn.close()
        dest_conn.close()


def migrate_collection_dirs(source_path: Path, dest_path: Path) -> None:
    """
    Migrate collection directories from source to destination.

    Parameters
    ----------
    source_path : Path
        Path to source vector store directory
    dest_path : Path
        Path to destination vector store directory
    """
    # Find UUID directories in source
    uuid_dirs = [
        d
        for d in source_path.iterdir()
        if d.is_dir() and len(d.name) == 36 and d.name.count("-") == 4
    ]

    copied_dirs = 0
    for uuid_dir in uuid_dirs:
        dest_uuid_dir = dest_path / uuid_dir.name

        if not dest_uuid_dir.exists():
            shutil.copytree(uuid_dir, dest_uuid_dir)
            copied_dirs += 1
            print(f"Copied collection directory: {uuid_dir.name}")
        else:
            print(f"Collection directory already exists: {uuid_dir.name}")

    print(f"Copied {copied_dirs} collection directories")


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description="Migrate vector store data from Eris to Ada"
    )
    parser.add_argument(
        "--source",
        "-s",
        default="./vector_stores/Eris/",
        help="Source vector store path (default: ./vector_stores/Eris/)",
    )
    parser.add_argument(
        "--dest",
        "-d",
        default="/home/alex/Dropbox/vector_stores/Ada/",
        help="Destination vector store path (default: /home/alex/Dropbox/vector_stores/Ada/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes",
    )

    args = parser.parse_args()

    source_path = Path(args.source)
    dest_path = Path(args.dest)

    # Validate paths
    if not source_path.exists():
        print(f"Error: Source path does not exist: {source_path}")
        return 1

    if not dest_path.exists():
        print(f"Error: Destination path does not exist: {dest_path}")
        return 1

    print(f"Migrating from: {source_path}")
    print(f"Migrating to: {dest_path}")

    if args.dry_run:
        print("DRY RUN - No changes will be made")
        # Count what would be migrated
        source_metadata = source_path / "metadata.json"
        if source_metadata.exists():
            with open(source_metadata, "r") as f:
                source_data = json.load(f)
            print(f"Would migrate {len(source_data)} exchanges from metadata")
        return 0

    print("Starting migration...")

    # Create backup of destination metadata
    dest_metadata = dest_path / "metadata.json"
    if dest_metadata.exists():
        backup_path = dest_path / "metadata.json.backup"
        shutil.copy2(dest_metadata, backup_path)
        print(f"Created backup: {backup_path}")

    try:
        # Migrate components
        print("\n1. Migrating metadata...")
        migrate_metadata(source_path, dest_path)

        print("\n2. Migrating ChromaDB...")
        migrate_chroma_db(source_path, dest_path)

        print("\n3. Migrating collection directories...")
        migrate_collection_dirs(source_path, dest_path)

        print("\nMigration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
