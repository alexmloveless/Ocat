#!/usr/bin/env python3
"""Debug script to check ChromaDB raw data"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ocat.config import Config
from ocat.vector_store import ConversationVectorStore


def main():
    config = Config.load("ocat.yaml")
    vector_store = ConversationVectorStore(config)

    print("Checking ChromaDB collection directly...")
    results = vector_store.collection.get()

    print(f"Total documents: {len(results.get('documents', []))}")

    docs = results.get("documents", []) or []
    metadatas = results.get("metadatas", []) or []
    ids = results.get("ids", []) or []

    print("\nChecking for productivity entities...")

    for i, (doc_id, metadata) in enumerate(zip(ids, metadatas)):
        if metadata and "entity_type" in metadata:
            print(f"\nFound productivity entity #{i+1}:")
            print(f"ID: {doc_id}")
            print(f"Metadata: {metadata}")
            print(f"Document: {docs[i] if i < len(docs) else 'N/A'}")
            print("-" * 50)

    # Count entities by type
    entity_types = {}
    for metadata in metadatas:
        if metadata and "entity_type" in metadata:
            entity_type = metadata["entity_type"]
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

    print(f"\nEntity type counts:")
    for entity_type, count in entity_types.items():
        print(f"  {entity_type}: {count}")

    if not entity_types:
        print("  No productivity entities found!")


if __name__ == "__main__":
    main()
