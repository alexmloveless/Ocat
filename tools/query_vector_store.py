#!/usr/bin/env python3
"""
Vector Store Query Tool

This tool allows you to query the vector store and see the raw stored data
exactly as it's stored, without any formatting or display labels.

Usage:
    python tools/query_vector_store.py --config <config_file> --query <search_text> [--results <n>]

Examples:
    python tools/query_vector_store.py --config local_config/ada_config.yaml --query "data scientist"
    python tools/query_vector_store.py --config local_config/ada_config.yaml --query "fact" --results 5
"""

import argparse
import sys
from pathlib import Path

# Add src to path so we can import ocat modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ocat.config import Config
from ocat.vector_store import ConversationVectorStore


def main():
    """Main function for the vector store query tool."""
    parser = argparse.ArgumentParser(
        description="Query vector store and show raw stored data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--config", type=str, required=True, help="Path to Ocat configuration file"
    )

    parser.add_argument("--query", type=str, required=True, help="Search query text")

    parser.add_argument(
        "--results",
        type=int,
        default=3,
        help="Number of results to return (default: 3)",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all exchanges in the vector store (ignores query)",
    )

    args = parser.parse_args()

    try:
        # Load configuration
        print(f"Loading config from: {args.config}")
        config = Config.load(args.config)

        # Initialize vector store
        print(f"Initializing vector store at: {config.vector_store.path}")
        vector_store = ConversationVectorStore(config)

        # Get stats
        stats = vector_store.get_stats()
        print(f"Total exchanges in store: {stats['total_exchanges']}")
        print(f"Vector store enabled: {config.vector_store.enabled}")
        print()

        if args.all:
            # Show all exchanges
            print("=== ALL EXCHANGES (RAW DATA) ===")
            for i, (exchange_id, exchange) in enumerate(vector_store.metadata.items()):
                print(f"Exchange #{i+1}")
                print(f"ID: {exchange_id}")
                print(f'User Prompt: "{exchange.user_prompt}"')
                print(f'Assistant Response: "{exchange.assistant_response}"')
                print(f"Thread ID: {exchange.thread_id}")
                print(f"Session ID: {exchange.session_id}")
                print(f"Timestamp: {exchange.timestamp}")
                print("-" * 80)
        else:
            # Query for similar exchanges
            print(f'Searching for: "{args.query}"')
            print(f"Returning top {args.results} results")
            print()

            similar_exchanges = vector_store.find_similar_exchanges(
                query_text=args.query, n_results=args.results
            )

            if not similar_exchanges:
                print("No similar exchanges found.")
                return 0

            print(f"=== QUERY RESULTS (RAW DATA) ===")
            for i, exchange in enumerate(similar_exchanges, 1):
                print(f"Result #{i}")
                print(f"Exchange ID: {exchange.exchange_id}")
                print(f'User Prompt: "{exchange.user_prompt}"')
                print(f'Assistant Response: "{exchange.assistant_response}"')
                print(f"Thread ID: {exchange.thread_id}")
                print(f"Session ID: {exchange.session_id}")
                print(f"Timestamp: {exchange.timestamp}")
                print(f"Prior Exchange IDs: {exchange.prior_exchange_ids}")
                print("-" * 80)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
