#!/usr/bin/env python3
"""
Test script to examine similarity scores and context retrieval in the eris vector store.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ocat.config import Config
from ocat.vector_store import ConversationVectorStore
from pathlib import Path
import yaml

def load_eris_config():
    """Load the eris configuration."""
    config_path = Path("/home/alex/repos/ocat/local/eris.yaml")
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    return Config(**config_data)

def test_similarity_scores():
    """Test similarity scores for various queries."""
    print("Loading eris configuration...")
    config = load_eris_config()
    
    print(f"Vector store path: {config.vector_store.path}")
    print(f"Similarity threshold: {config.vector_store.similarity_threshold}")
    print(f"Context results: {config.vector_store.context_results}")
    
    # Initialize vector store
    vector_store = ConversationVectorStore(config)
    
    print(f"\nTotal exchanges in vector store: {len(vector_store.metadata)}")
    
    if len(vector_store.metadata) == 0:
        print("No exchanges found in vector store!")
        return
    
    # Show some sample exchanges
    print("\nSample exchanges in vector store:")
    for i, (exchange_id, exchange) in enumerate(list(vector_store.metadata.items())[:3]):
        print(f"\n{i+1}. Exchange ID: {exchange_id}")
        print(f"   User: {exchange.user_prompt[:100]}...")
        print(f"   Assistant: {exchange.assistant_response[:100]}...")
        print(f"   Thread ID: {exchange.thread_id}")
    
    # Test queries
    test_queries = [
        "How are you today?",
        "Tell me about Python programming",
        "What's the weather like?",
        "User: Hello Assistant: Hi there! How can I help you today?",
        "explain context functionality",
        "how does ocat work"
    ]
    
    print("\n" + "="*80)
    print("TESTING SIMILARITY QUERIES")
    print("="*80)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 60)
        
        try:
            # Get raw ChromaDB results to see distances
            results = vector_store.collection.query(
                query_texts=[query], 
                n_results=10  # Get more results to see score distribution
            )
            
            print(f"Raw ChromaDB results found: {len(results['ids'][0])}")
            
            if results['distances'] and results['distances'][0]:
                print("Top results with distances (lower = more similar):")
                for i, (exchange_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                    if exchange_id in vector_store.metadata:
                        exchange = vector_store.metadata[exchange_id]
                        similarity = 1.0 - distance  # Convert distance to similarity
                        above_threshold = similarity >= config.vector_store.similarity_threshold
                        
                        print(f"  {i+1}. Distance: {distance:.4f}, Similarity: {similarity:.4f} {'✓' if above_threshold else '✗'}")
                        print(f"      User: {exchange.user_prompt[:80]}...")
                        print(f"      Assistant: {exchange.assistant_response[:60]}...")
                        print()
            
            # Now test the actual find_similar_exchanges method
            similar_exchanges = vector_store.find_similar_exchanges(
                query, 
                n_results=5,
                exclude_memories=True
            )
            
            print(f"find_similar_exchanges returned: {len(similar_exchanges)} results")
            
            # Test get_episodic_context method
            context_exchanges = vector_store.get_episodic_context(
                query_text=query,
                max_context_length=2000,
                relevance_threshold=config.vector_store.similarity_threshold
            )
            
            print(f"get_episodic_context returned: {len(context_exchanges)} results")
            
        except Exception as e:
            print(f"Error testing query: {e}")
    
    print("\n" + "="*80)
    print("CONFIGURATION ANALYSIS")
    print("="*80)
    print(f"Similarity threshold: {config.vector_store.similarity_threshold}")
    print("Note: With threshold 0.1, almost everything should be included!")
    print(f"Context results requested: {config.vector_store.context_results}")
    print(f"Search context window: {config.vector_store.search_context_window}")

if __name__ == "__main__":
    test_similarity_scores()