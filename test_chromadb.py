#!/usr/bin/env python3
"""
Test ChromaDB access without triggering compaction.
"""
import os
from chromadb import Client
from chromadb.config import Settings


def test_chromadb_access():
    """Test basic ChromaDB access without triggering compaction."""

    # Disable telemetry
    os.environ["ANONYMIZED_TELEMETRY"] = "False"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    db_path = "/home/alex/Dropbox/vector_stores/Ada"

    try:
        # Try to create client with minimal settings
        settings = Settings(
            persist_directory=db_path,
            is_persistent=True,
            anonymized_telemetry=False,
        )

        print("Creating ChromaDB client...")
        client = Client(settings)

        # Try to get collection without listing (listing might trigger compaction)
        print("Attempting to get 'conversation' collection...")
        collection = client.get_collection("conversation")

        print(f"Success! Collection has {collection.count()} items")

        # Try a simple query that doesn't trigger compaction
        print("Attempting simple query...")
        results = collection.get(limit=1)

        if results and results.get("ids"):
            print(f"Retrieved {len(results['ids'])} items successfully")
            print(
                "ChromaDB is accessible - compaction may only affect specific operations"
            )
            return True
        else:
            print("No results returned")

    except Exception as e:
        print(f"Access failed: {e}")
        return False


if __name__ == "__main__":
    test_chromadb_access()
