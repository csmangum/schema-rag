#!/usr/bin/env python3
"""Build FAISS index from schema RAG documents.

This script:
1. Loads documents from JSONL
2. Generates embeddings using sentence-transformers
3. Creates FAISS IndexFlatL2 index
4. Saves index and metadata
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

try:
    import faiss
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(f"Error: Missing required dependencies. Please install: pip install faiss-cpu sentence-transformers")
    print(f"Import error: {e}")
    exit(1)


def load_documents(jsonl_path: Path) -> List[Dict[str, Any]]:
    """Load documents from JSONL file."""
    documents = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                documents.append(json.loads(line))
    return documents


def build_index(
    documents: List[Dict[str, Any]],
    model_name: str = "all-MiniLM-L6-v2",
    output_dir: Path = None,
) -> None:
    """Build FAISS index from documents."""
    print(f"Loading embedding model: {model_name}...")
    model = SentenceTransformer(model_name)
    
    # Extract texts for embedding
    texts = [doc["text"] for doc in documents]
    
    print(f"Generating embeddings for {len(texts)} documents...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    
    dimension = embeddings.shape[1]
    print(f"Embedding dimension: {dimension}")
    
    # Create FAISS index
    print("Creating FAISS index...")
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    print(f"Index contains {index.ntotal} vectors")
    
    # Save index
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        index_path = output_dir / "faiss.index"
        print(f"Saving index to {index_path}...")
        faiss.write_index(index, str(index_path))
        
        # Save documents metadata
        docs_path = output_dir / "docs.jsonl"
        print(f"Saving document metadata to {docs_path}...")
        with open(docs_path, "w", encoding="utf-8") as f:
            for doc in documents:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        
        # Save config
        config_path = output_dir / "config.json"
        config = {
            "dimension": dimension,
            "model_name": model_name,
            "num_documents": len(documents),
        }
        print(f"Saving config to {config_path}...")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        
        print(f"✓ Index built successfully")
        print(f"  Index file: {index_path}")
        print(f"  Documents: {docs_path}")
        print(f"  Config: {config_path}")


def main():
    parser = argparse.ArgumentParser(description="Build FAISS index from schema RAG documents")
    parser.add_argument(
        "--docs",
        type=str,
        required=True,
        help="Input JSONL file with documents",
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output directory for index files",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="all-MiniLM-L6-v2",
        help="Sentence transformer model name (default: all-MiniLM-L6-v2)",
    )
    args = parser.parse_args()
    
    docs_path = Path(args.docs)
    output_dir = Path(args.out)
    
    if not docs_path.exists():
        print(f"Error: Documents file not found: {docs_path}")
        return 1
    
    print(f"Loading documents from {docs_path}...")
    documents = load_documents(docs_path)
    print(f"Loaded {len(documents)} documents")
    
    build_index(documents, model_name=args.model, output_dir=output_dir)
    
    return 0


if __name__ == "__main__":
    exit(main())
