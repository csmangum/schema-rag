# schema-rag

Schema-aware RAG (Retrieval Augmented Generation) service for retrieving database schema information using natural language queries.

## Overview

Schema RAG enables agents and LLMs to ground their responses in database schema information by:
- Embedding schema documentation (models, columns) and query recipes into a FAISS vector index
- Using hybrid retrieval (vector similarity + lexical matching) to find relevant schema information
- Returning structured references, join hints, and query recipes

## Features

- **Hybrid Retrieval**: Multi-component scoring system combining semantic vector search, lexical matching, exact match detection, and pattern recognition
- **High Precision**: Achieves 80.9% precision for model+column matching (96.4% for model matching)
- **Query Expansion**: Bidirectional synonym expansion with multi-word phrase support (2-4 word phrases)
- **Entity Extraction**: Extracts program names, dates, temporal types, and numeric filters from questions
- **Recipe Prioritization**: Curated query recipes are prioritized with pattern-based boosts
- **Intelligent Penalties**: Demotes incorrect matches to improve precision
- **Join Hint Generation**: Automatically generates join paths for related tables
- **Ambiguity Detection**: Identifies semantic ambiguities (e.g., variant_id handling)

## Installation

```bash
pip install -r requirements.txt
```

Or install dependencies individually:
```bash
pip install faiss-cpu sentence-transformers
```

## Quick Start

### 1. Generate Documents from Schema JSON

First, you need a schema JSON file. If you're using SQLAlchemy, you can export your models to JSON (see example export script), or provide your own schema JSON in this format:

```json
{
  "models": [
    {
      "model": "ProgramStatistics",
      "module": "models",
      "table": "program_statistics",
      "columns": [
        {
          "name": "success_count",
          "type": "Integer",
          "nullable": false
        }
      ],
      "relationships": []
    }
  ]
}
```

Generate RAG documents:
```bash
python scripts/generate_schema_rag_docs.py \
  --schema artifacts/sqlalchemy_models.json \
  --out artifacts/schema_rag_docs.jsonl
```

### 2. Build FAISS Index

```bash
python scripts/build_schema_rag_index.py \
  --docs artifacts/schema_rag_docs.jsonl \
  --out artifacts/schema_rag_index/
```

### 3. Query the Index

**Command-line:**
```bash
python scripts/query_schema_rag.py "What is the success count for the forest fire program"
```

**Python API:**
```python
from schema_rag import SchemaRagService
from pathlib import Path

# Initialize service
service = SchemaRagService(Path("artifacts/schema_rag_index"))

# Query
result = service.retrieve_grounding(
    "What is the success count for the forest fire program",
    top_k=5
)

# Access results
print("Schema References:")
for ref in result.schema_refs:
    print(f"  {ref['model']}.{ref['column']} (table: {ref['table']})")

print("\nJoin Hints:")
for hint in result.join_hints:
    print(f"  {hint}")

print("\nRecipes:")
for recipe in result.recipes:
    print(f"  {recipe['id']}: {recipe['text'][:100]}...")
```

## Usage

### SchemaRagService

The main service class for querying the schema index:

```python
from schema_rag import SchemaRagService, GroundingResult
from pathlib import Path

service = SchemaRagService(Path("artifacts/schema_rag_index"))
result: GroundingResult = service.retrieve_grounding(
    question="How many failures for program forest fire?",
    top_k=5
)
```

### GroundingResult

The result object contains:

- `docs`: List of retrieved documents with scores
- `schema_refs`: Normalized schema references (model.table.column)
- `join_hints`: Join path strings for related tables
- `recipes`: Query recipe matches with join patterns
- `ambiguities`: Semantic notes about potential ambiguities

## Document Types

The system generates three types of documents:

1. **schema_model**: One per ORM model (describes the model and its relationships)
2. **schema_column**: One per column (describes the column with natural language aliases)
3. **query_recipe**: Template-generated recipes for common query patterns (includes join hints)

## Architecture

See [docs/SCHEMA_RAG.md](docs/SCHEMA_RAG.md) for detailed architecture documentation.

## Scripts

- `scripts/generate_schema_rag_docs.py`: Generate RAG documents from schema JSON
- `scripts/build_schema_rag_index.py`: Build FAISS index from documents
- `scripts/query_schema_rag.py`: Command-line query tool

## Testing

Comprehensive test results are available:
- [artifacts/SCHEMA_RAG_TEST_REPORT.md](artifacts/SCHEMA_RAG_TEST_REPORT.md) - Original test report
- [artifacts/SCORING_REFINEMENT_TEST_RESULTS.md](artifacts/SCORING_REFINEMENT_TEST_RESULTS.md) - Latest test results after scoring improvements

The test suite evaluates the system with 110 natural language questions and shows:
- **80.9% precision** for model+column matching (up from 58.2%)
- **96.4% precision** for model matching (up from 67.3%)
- **38.1% improvement** in average top scores
- **162% increase** in average schema references per query

## Configuration

### Synonyms

Edit `schema_rag/schema_synonyms.json` to customize query expansion. The system supports:
- **Bidirectional expansion**: Synonyms work in both directions (e.g., "run" → "usage" and "usage" → "run")
- **Multi-word phrases**: Support for 2-4 word phrases (e.g., "how many times" → "usage_count")
- **Comprehensive coverage**: Includes synonyms for execution, status, temporal, and descriptive terms

Example:
```json
{
  "run": ["usage", "execution", "executed", "usage_count", "executions"],
  "how many times": ["usage_count", "count", "executions"],
  "status": ["running", "completed", "active", "inactive", "state"]
}
```

### Curated Recipes

Curated recipes receive higher priority in search results with pattern-based boosts:
- **Base boost**: +4.0 for curated recipes
- **Pattern boosts**: +2.0 for matching patterns (aggregation, temporal, status, relationship)

You can add curated recipes by creating a JSONL file and passing it to the document generator:

```bash
python scripts/generate_schema_rag_docs.py \
  --schema artifacts/sqlalchemy_models.json \
  --out artifacts/schema_rag_docs.jsonl \
  --curated artifacts/schema_rag_curated_recipes.jsonl
```

Curated recipes should include metadata like `recipe_type` (aggregation, temporal, status, relationship) to enable pattern-based boosting.

## Requirements

- Python 3.8+
- faiss-cpu>=1.7.4
- sentence-transformers>=2.2.0

## License

MIT

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
