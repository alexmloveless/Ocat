#!/usr/bin/env python3
"""
Chroma Database Backup and Restore Utility

This script provides functionality to backup, compress, restore, and uncompress
Chroma vector databases. It supports tar.gz compression for efficient storage
and transfer of database files.
"""

import argparse
import logging
import shutil
import tarfile
from pathlib import Path
from typing import Optional


def setup_logging(verbose: bool = False) -> None:
    """
    Set up logging configuration.

    Parameters
    ----------
    verbose : bool, optional
        Enable verbose logging, by default False
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def backup_chroma_db(db_path: Path, backup_path: Path, compress: bool = True) -> None:
    """
    Backup a Chroma database directory.

    Parameters
    ----------
    db_path : Path
        Path to the Chroma database directory
    backup_path : Path
        Path where the backup will be stored
    compress : bool, optional
        Whether to compress the backup, by default True

    Raises
    ------
    FileNotFoundError
        If the source database directory doesn't exist
    PermissionError
        If insufficient permissions to read source or write destination
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database path does not exist: {db_path}")

    if not db_path.is_dir():
        raise ValueError(f"Database path is not a directory: {db_path}")

    logging.info(f"Starting backup of {db_path}")

    if compress:
        # Ensure backup path has .tar.gz extension
        if not backup_path.name.endswith(".tar.gz"):
            backup_path = backup_path.with_suffix(".tar.gz")

        # Create compressed backup
        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(db_path, arcname=db_path.name)

        logging.info(f"Compressed backup created: {backup_path}")
    else:
        # Create uncompressed backup (copy directory)
        if backup_path.exists():
            shutil.rmtree(backup_path)

        shutil.copytree(db_path, backup_path)
        logging.info(f"Uncompressed backup created: {backup_path}")


def restore_chroma_db(
    backup_path: Path, restore_path: Path, overwrite: bool = False
) -> None:
    """
    Restore a Chroma database from backup.

    Parameters
    ----------
    backup_path : Path
        Path to the backup file or directory
    restore_path : Path
        Path where the database will be restored
    overwrite : bool, optional
        Whether to overwrite existing database, by default False

    Raises
    ------
    FileNotFoundError
        If the backup file/directory doesn't exist
    FileExistsError
        If restore path exists and overwrite is False
    """
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup path does not exist: {backup_path}")

    if restore_path.exists() and not overwrite:
        raise FileExistsError(
            f"Restore path already exists: {restore_path}. Use --overwrite to replace it."
        )

    logging.info(f"Starting restore from {backup_path}")

    # Remove existing directory if overwriting
    if restore_path.exists() and overwrite:
        logging.info(f"Removing existing directory: {restore_path}")
        shutil.rmtree(restore_path)

    if backup_path.suffix == ".gz" or backup_path.name.endswith(".tar.gz"):
        # Extract compressed backup
        with tarfile.open(backup_path, "r:gz") as tar:
            # Extract to parent directory of restore_path
            tar.extractall(path=restore_path.parent)

            # Get the extracted directory name (first member's name)
            extracted_name = tar.getnames()[0].split("/")[0]
            extracted_path = restore_path.parent / extracted_name

            # Rename to desired restore path if different
            if extracted_path != restore_path:
                extracted_path.rename(restore_path)

        logging.info(f"Database restored from compressed backup to: {restore_path}")
    else:
        # Copy uncompressed backup
        shutil.copytree(backup_path, restore_path)
        logging.info(f"Database restored from uncompressed backup to: {restore_path}")


def get_backup_info(backup_path: Path) -> dict:
    """
    Get information about a backup file.

    Parameters
    ----------
    backup_path : Path
        Path to the backup file or directory

    Returns
    -------
    dict
        Dictionary containing backup information
    """
    if not backup_path.exists():
        return {"error": "Backup path does not exist"}

    info = {
        "path": str(backup_path),
        "exists": True,
        "type": (
            "compressed"
            if backup_path.suffix == ".gz" or backup_path.name.endswith(".tar.gz")
            else "uncompressed"
        ),
        "size_bytes": 0,
    }

    if backup_path.is_file():
        info["size_bytes"] = backup_path.stat().st_size
        info["size_mb"] = round(info["size_bytes"] / (1024 * 1024), 2)
    elif backup_path.is_dir():
        # Calculate directory size
        total_size = sum(
            f.stat().st_size for f in backup_path.rglob("*") if f.is_file()
        )
        info["size_bytes"] = total_size
        info["size_mb"] = round(total_size / (1024 * 1024), 2)

    return info


def main() -> None:
    """Main function to handle command line arguments and execute operations."""
    parser = argparse.ArgumentParser(
        description="Backup, compress, restore, and uncompress Chroma databases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backup and compress a database
  %(prog)s backup /path/to/chroma/db /path/to/backup.tar.gz

  # Backup without compression
  %(prog)s backup /path/to/chroma/db /path/to/backup_dir --no-compress

  # Restore from compressed backup
  %(prog)s restore /path/to/backup.tar.gz /path/to/restored/db

  # Restore with overwrite
  %(prog)s restore /path/to/backup.tar.gz /path/to/restored/db --overwrite

  # Get backup information
  %(prog)s info /path/to/backup.tar.gz
        """,
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Backup a Chroma database")
    backup_parser.add_argument(
        "db_path", type=Path, help="Path to the Chroma database directory"
    )
    backup_parser.add_argument(
        "backup_path", type=Path, help="Path for the backup file/directory"
    )
    backup_parser.add_argument(
        "--no-compress", action="store_true", help="Skip compression"
    )

    # Restore command
    restore_parser = subparsers.add_parser(
        "restore", help="Restore a Chroma database from backup"
    )
    restore_parser.add_argument(
        "backup_path", type=Path, help="Path to the backup file/directory"
    )
    restore_parser.add_argument(
        "restore_path", type=Path, help="Path where database will be restored"
    )
    restore_parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing database"
    )

    # Info command
    info_parser = subparsers.add_parser("info", help="Get information about a backup")
    info_parser.add_argument(
        "backup_path", type=Path, help="Path to the backup file/directory"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    setup_logging(args.verbose)

    try:
        if args.command == "backup":
            backup_chroma_db(
                db_path=args.db_path,
                backup_path=args.backup_path,
                compress=not args.no_compress,
            )

        elif args.command == "restore":
            restore_chroma_db(
                backup_path=args.backup_path,
                restore_path=args.restore_path,
                overwrite=args.overwrite,
            )

        elif args.command == "info":
            info = get_backup_info(args.backup_path)
            if "error" in info:
                logging.error(info["error"])
                return

            print(f"Backup Information:")
            print(f"  Path: {info['path']}")
            print(f"  Type: {info['type']}")
            print(f"  Size: {info['size_mb']} MB ({info['size_bytes']} bytes)")

    except Exception as e:
        logging.error(f"Operation failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
