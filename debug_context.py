#!/usr/bin/env python3
"""
Debug script to identify why context isn't being retrieved properly.
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

def debug_context_retrieval():
    """Debug the context retrieval issue."""
    print("="*80)
    print("DEBUGGING CONTEXT RETRIEVAL ISSUE")
    print("="*80)
    
    config = load_eris_config()
    vector_store = ConversationVectorStore(config)
    
    print(f"Total exchanges: {len(vector_store.metadata)}")
    print(f"Similarity threshold: {config.vector_store.similarity_threshold}")
    print(f"Context results: {config.vector_store.context_results}")
    
    # Test a typical query
    query = "tell me about programming"
    
    print(f"\nTesting query: '{query}'")
    print("-" * 50)
    
    # 1. Test raw ChromaDB query
    print("1. Raw ChromaDB results:")
    results = vector_store.collection.query(
        query_texts=[query], 
        n_results=10
    )
    
    above_threshold_count = 0
    for i, (exchange_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
        if exchange_id in vector_store.metadata:
            similarity = 1.0 - distance
            above_threshold = similarity >= config.vector_store.similarity_threshold
            if above_threshold:
                above_threshold_count += 1
            
            print(f"  {i+1}. Similarity: {similarity:.4f} {'✓' if above_threshold else '✗'}")
            
            if i < 3:  # Show first few
                exchange = vector_store.metadata[exchange_id]
                print(f"      User: {exchange.user_prompt[:60]}...")
    
    print(f"\nResults above threshold (0.1): {above_threshold_count}")
    
    # 2. Test find_similar_exchanges
    print(f"\n2. find_similar_exchanges results:")
    similar = vector_store.find_similar_exchanges(query, n_results=5, exclude_memories=True)
    print(f"   Returned: {len(similar)} exchanges")
    
    # 3. Test get_episodic_context with different parameters
    print(f"\n3. get_episodic_context tests:")
    
    # Test with current config
    context1 = vector_store.get_episodic_context(
        query_text=query,
        max_context_length=2000,
        relevance_threshold=config.vector_store.similarity_threshold
    )
    print(f"   Current config: {len(context1)} results")
    
    # Test with no relevance threshold (should include all)
    context2 = vector_store.get_episodic_context(
        query_text=query,
        max_context_length=2000,
        relevance_threshold=0.0
    )
    print(f"   No threshold: {len(context2)} results")
    
    # Test with higher length limit
    context3 = vector_store.get_episodic_context(
        query_text=query,
        max_context_length=10000,
        relevance_threshold=config.vector_store.similarity_threshold
    )
    print(f"   Higher length limit: {len(context3)} results")
    
    # 4. Check the smart pruning logic
    print(f"\n4. Character length analysis:")
    if len(similar) > 0:
        total_chars = 0
        for i, ex in enumerate(similar):
            ex_chars = len(ex.user_prompt) + len(ex.assistant_response)
            total_chars += ex_chars
            print(f"   Exchange {i+1}: {ex_chars} chars (total so far: {total_chars})")
            if total_chars > 2000:
                print(f"   ^ Would be excluded by 2000 char limit")
                break
    
    print(f"\n" + "="*80)
    print("KEY FINDINGS:")
    print("="*80)
    print(f"• ChromaDB finds {len(results['ids'][0])} results")
    print(f"• {above_threshold_count} are above similarity threshold (0.1)")
    print(f"• find_similar_exchanges returns {len(similar)}")
    print(f"• get_episodic_context returns {len(context1)} (with current config)")
    print(f"• get_episodic_context returns {len(context2)} (with no threshold)")
    print("\nThe issue is likely in the character-based pruning in get_episodic_context!")

if __name__ == "__main__":
    debug_context_retrieval()