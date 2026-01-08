#!/usr/bin/env python3
"""Query schema RAG index from command line.

Example:
    python scripts/query_schema_rag.py "What is the success count for the forest fire program"
"""

import argparse
import json
import sys
from pathlib import Path

# Add schema_rag package to path
package_path = Path(__file__).parent.parent
sys.path.insert(0, str(package_path))

from schema_rag import SchemaRagService


def format_grounding_result(result) -> str:
    """Format grounding result for display."""
    lines = []
    
    lines.append("=" * 80)
    lines.append("SCHEMA GROUNDING RESULT")
    lines.append("=" * 80)
    lines.append("")
    
    # Documents
    lines.append(f"Retrieved Documents ({len(result.docs)}):")
    lines.append("-" * 80)
    for i, doc in enumerate(result.docs, 1):
        lines.append(f"\n{i}. {doc['doc_type']} (score: {doc['score']:.4f})")
        lines.append(f"   ID: {doc['id']}")
        lines.append(f"   Text: {doc['text'][:200]}...")
        if doc.get('vector_score'):
            lines.append(f"   Vector score: {doc['vector_score']:.4f}")
        if doc.get('lexical_boost'):
            lines.append(f"   Lexical boost: {doc['lexical_boost']:.4f}")
    lines.append("")
    
    # Schema references
    if result.schema_refs:
        lines.append(f"Schema References ({len(result.schema_refs)}):")
        lines.append("-" * 80)
        for ref in result.schema_refs:
            lines.append(f"  - {ref['model']}.{ref['column']} (table: {ref['table']})")
            if ref.get('source_file'):
                lines.append(f"    Source: {ref['source_file']}")
        lines.append("")
    
    # Join hints
    if result.join_hints:
        lines.append(f"Join Hints ({len(result.join_hints)}):")
        lines.append("-" * 80)
        for hint in result.join_hints:
            lines.append(f"  - {hint}")
        lines.append("")
    
    # Recipes
    if result.recipes:
        lines.append(f"Query Recipes ({len(result.recipes)}):")
        lines.append("-" * 80)
        for recipe in result.recipes:
            lines.append(f"  - {recipe['id']}")
            lines.append(f"    {recipe['text'][:200]}...")
            if recipe.get('join_hints'):
                lines.append(f"    Join hints: {', '.join(recipe['join_hints'])}")
        lines.append("")
    
    # Ambiguities
    if result.ambiguities:
        lines.append(f"Ambiguities ({len(result.ambiguities)}):")
        lines.append("-" * 80)
        for ambiguity in result.ambiguities:
            lines.append(f"  - {ambiguity}")
        lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Query schema RAG index")
    parser.add_argument(
        "question",
        type=str,
        help="Natural language question about the database schema",
    )
    parser.add_argument(
        "--index",
        type=str,
        default="artifacts/schema_rag_index",
        help="Path to schema RAG index directory",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of documents to retrieve (default: 5)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of formatted text",
    )
    args = parser.parse_args()
    
    index_path = Path(args.index)
    
    if not index_path.exists():
        print(f"Error: Index path does not exist: {index_path}")
        print("Run the build scripts first:")
        print("  1. python scripts/generate_schema_rag_docs.py --schema <schema.json> --out artifacts/schema_rag_docs.jsonl")
        print("  2. python scripts/build_schema_rag_index.py --docs artifacts/schema_rag_docs.jsonl --out artifacts/schema_rag_index/")
        return 1
    
    try:
        print(f"Loading schema RAG service from {index_path}...")
        service = SchemaRagService(index_path)
        
        print(f"Querying: {args.question}")
        print("")
        
        result = service.retrieve_grounding(args.question, top_k=args.top_k)
        
        if args.json:
            # Output as JSON
            output = {
                "query": args.question,
                "docs": result.docs,
                "schema_refs": result.schema_refs,
                "join_hints": result.join_hints,
                "recipes": result.recipes,
                "ambiguities": result.ambiguities,
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            # Output formatted text
            print(format_grounding_result(result))
        
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
