#!/usr/bin/env python3
"""
ChromaDB repair utility to fix compaction errors.
"""
import os
import shutil
from pathlib import Path
from chromadb import Client
from chromadb.config import Settings


def repair_chromadb(db_path: str):
    """Attempt to repair ChromaDB by recreating collections without compaction."""
    print(f"Attempting to repair ChromaDB at: {db_path}")

    try:
        # Disable telemetry to prevent further errors
        os.environ["ANONYMIZED_TELEMETRY"] = "False"
        os.environ["TOKENIZERS_PARALLELISM"] = "false"

        # Try to create a new ChromaDB instance in a temp location
        temp_path = f"{db_path}_temp_repair"
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)

        # Create settings that bypass compaction issues
        temp_settings = Settings(
            persist_directory=temp_path,
            is_persistent=True,
            anonymized_telemetry=False,
        )

        print("Creating temporary ChromaDB instance...")
        temp_client = Client(temp_settings)

        # Try to access the original database directly via SQLite to extract data
        import sqlite3

        conn = sqlite3.connect(f"{db_path}/chroma.sqlite3")
        cursor = conn.cursor()

        # Get collection information
        cursor.execute("SELECT name, id FROM collections")
        collections_data = cursor.fetchall()
        print(f"Found {len(collections_data)} collections in SQLite:")

        for coll_name, coll_id in collections_data:
            print(f"  - Collection: {coll_name} (ID: {coll_id})")

            # Create collection in temp database
            temp_collection = temp_client.create_collection(coll_name)

            # Extract embeddings and metadata from SQLite
            cursor.execute(
                "SELECT id, embedding, document, metadata FROM embeddings WHERE collection_id = ?",
                (coll_id,),
            )
            embeddings_data = cursor.fetchall()
            print(f"    Found {len(embeddings_data)} embeddings")

            if embeddings_data:
                # Prepare data for batch insertion
                ids = []
                documents = []
                metadatas = []
                embeddings = []

                for emb_id, embedding, document, metadata in embeddings_data:
                    ids.append(emb_id)
                    documents.append(document or "")

                    # Parse metadata JSON if it exists
                    import json

                    try:
                        metadata_dict = json.loads(metadata) if metadata else {}
                    except:
                        metadata_dict = {}
                    metadatas.append(metadata_dict)

                    # Parse embedding blob
                    import pickle

                    try:
                        embedding_vector = (
                            pickle.loads(embedding) if embedding else None
                        )
                        if embedding_vector is not None:
                            embeddings.append(embedding_vector)
                        else:
                            # Skip this entry if no embedding
                            ids.pop()
                            documents.pop()
                            metadatas.pop()
                    except:
                        # Skip this entry if embedding can't be parsed
                        ids.pop()
                        documents.pop()
                        metadatas.pop()

                # Add to temporary collection
                if ids:
                    temp_collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas,
                        embeddings=embeddings if embeddings else None,
                    )
                    print(f"    Transferred {len(ids)} valid embeddings")

        conn.close()

        # Replace original with repaired version
        print("Replacing original database with repaired version...")
        backup_path = f"{db_path}_backup_{int(time.time())}"
        shutil.move(db_path, backup_path)
        shutil.move(temp_path, db_path)

        print(f"Repair completed successfully!")
        print(f"Original backed up to: {backup_path}")
        return True

    except Exception as e:
        print(f"Repair failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    import time

    repair_chromadb("/home/alex/Dropbox/vector_stores/Ada")
