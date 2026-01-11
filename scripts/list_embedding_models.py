#!/usr/bin/env python3
"""List available sentence-transformers models and their specifications."""

from sentence_transformers import SentenceTransformer

# Models to check - organized by tier
models_to_check = {
    "Tier 1 (Lightweight)": [
        "all-MiniLM-L6-v2",
        "all-MiniLM-L12-v2",
    ],
    "Tier 2 (Balanced)": [
        "all-mpnet-base-v2",
        "multi-qa-mpnet-base-dot-v1",
        "paraphrase-mpnet-base-v2",
    ],
    "Tier 3 (Large)": [
        "all-roberta-large-v1",
        "paraphrase-multilingual-mpnet-base-v2",
    ],
    "Tier 4 (State-of-the-Art)": [
        "intfloat/e5-large-v2",
        "BAAI/bge-large-en-v1.5",
        "thenlper/gte-large",
        "sentence-transformers/all-mpnet-base-v2",  # Same as all-mpnet-base-v2
    ],
}

def get_model_info(model_name: str) -> dict:
    """Get information about a model."""
    try:
        print(f"  Loading {model_name}...", end=" ", flush=True)
        model = SentenceTransformer(model_name)
        dim = model.get_sentence_embedding_dimension()
        print(f"✓ {dim} dims")
        return {
            "name": model_name,
            "dimensions": dim,
            "available": True,
        }
    except Exception as e:
        print(f"✗ Error: {str(e)[:50]}")
        return {
            "name": model_name,
            "dimensions": None,
            "available": False,
            "error": str(e)[:100],
        }

def main():
    print("=" * 80)
    print("SENTENCE-TRANSFORMERS MODEL HIERARCHY")
    print("=" * 80)
    print()
    
    all_results = {}
    
    for tier, models in models_to_check.items():
        print(f"{tier}:")
        print("-" * 80)
        tier_results = []
        
        for model_name in models:
            info = get_model_info(model_name)
            tier_results.append(info)
        
        all_results[tier] = tier_results
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    available_models = []
    for tier, results in all_results.items():
        for result in results:
            if result.get("available"):
                available_models.append({
                    "tier": tier,
                    "name": result["name"],
                    "dims": result["dimensions"],
                })
    
    # Sort by dimensions
    available_models.sort(key=lambda x: x["dims"])
    
    print(f"{'Model':<50} {'Tier':<25} {'Dimensions':<12}")
    print("-" * 80)
    for model in available_models:
        print(f"{model['name']:<50} {model['tier']:<25} {model['dims']:<12}")
    
    print()
    print(f"Total available models: {len(available_models)}")
    
    # Recommendations
    print()
    print("=" * 80)
    print("RECOMMENDATIONS FOR SCHEMA RAG")
    print("=" * 80)
    print()
    print("Based on your current comparison:")
    print("  • Tier 1: Fastest, good for low-latency requirements")
    print("  • Tier 2: Best balance (all-mpnet-base-v2 currently winning)")
    print("  • Tier 3: Higher accuracy, slower queries")
    print("  • Tier 4: State-of-the-art, may require more resources")
    print()
    print("Next models to test:")
    for tier in ["Tier 3 (Large)", "Tier 4 (State-of-the-Art)"]:
        if tier in all_results:
            for result in all_results[tier]:
                if result.get("available"):
                    print(f"  • {result['name']} ({result['dimensions']} dims)")
                    break
    
    return 0

if __name__ == "__main__":
    exit(main())
