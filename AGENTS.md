# AGENTS.md - AI Agent Instructions for Schema RAG

This file provides instructions and context for AI agents working on the Schema RAG codebase.

## Project Overview

**Schema RAG** is a schema-aware Retrieval Augmented Generation (RAG) service that enables agents and LLMs to retrieve database schema information using natural language queries. It uses FAISS vector search combined with hybrid scoring (lexical matching, entity extraction, pattern boosting) to achieve high-precision schema retrieval.

### Key Capabilities

- Embeds schema documentation (models, columns) and query recipes into a FAISS vector index
- Uses hybrid retrieval combining vector similarity + lexical matching + entity extraction
- Returns structured references, join hints, and query recipes
- Achieves **82.6% precision** for model+column matching with **100% query success rate**

## Technology Stack

- **Python 3.8+**
- **FAISS** (faiss-cpu) - Vector similarity search
- **Sentence Transformers** - Embedding generation (default: `all-MiniLM-L6-v2`)
- **pytest** - Testing framework

## Directory Structure

```
/workspace/
├── schema_rag/              # Main Python package
│   ├── __init__.py          # Package exports (SchemaRagService, GroundingResult)
│   ├── service.py           # Core SchemaRagService implementation
│   └── schema_synonyms.json # Query expansion synonym dictionary
├── scripts/                 # Utility scripts for building/querying
│   ├── generate_schema_rag_docs.py   # Generate RAG documents from schema JSON
│   ├── build_schema_rag_index.py     # Build FAISS index from documents
│   ├── query_schema_rag.py           # CLI query tool
│   ├── introspect_mssql_schema.py    # MSSQL schema introspection
│   ├── test_schema_rag_comprehensive.py  # Comprehensive test suite
│   ├── compare_embedding_models.py   # Embedding model comparison
│   └── generate_comparison_charts.py # Generate performance charts
├── tests/                   # Unit tests
│   ├── test_service.py      # SchemaRagService unit tests
│   └── README.md            # Test documentation
├── artifacts/               # Generated artifacts (indexes, reports, charts)
│   ├── schema_rag_index/    # Default FAISS index directory
│   ├── sqlalchemy_models.json        # Sample schema JSON
│   ├── schema_rag_docs.jsonl         # Generated documents
│   └── *.md                 # Test reports and documentation
├── docs/
│   └── SCHEMA_RAG.md        # Architecture documentation
├── requirements.txt         # Python dependencies
├── pytest.ini               # Pytest configuration
└── README.md                # Project README
```

## Environment Setup

### Install Dependencies

```bash
pip install -r requirements.txt
```

The core dependencies are:
- `faiss-cpu>=1.7.4`
- `sentence-transformers>=2.2.0`
- `pytest>=7.0.0` (for testing)

### Verify Installation

```bash
python -c "import faiss; from sentence_transformers import SentenceTransformer; print('OK')"
```

## Key Commands

### Build the RAG Index

```bash
# 1. Generate documents from schema JSON
python scripts/generate_schema_rag_docs.py \
  --schema artifacts/sqlalchemy_models.json \
  --out artifacts/schema_rag_docs.jsonl \
  --dialect postgresql

# 2. Build FAISS index
python scripts/build_schema_rag_index.py \
  --docs artifacts/schema_rag_docs.jsonl \
  --out artifacts/schema_rag_index/
```

### Query the Index (CLI)

```bash
python scripts/query_schema_rag.py "What is the success count for the forest fire program"
```

### Run Tests

```bash
# Run all unit tests
pytest

# Run with coverage
pytest --cov=schema_rag

# Run specific test class
pytest tests/test_service.py::TestRetrieveGrounding

# Run comprehensive integration tests
python scripts/test_schema_rag_comprehensive.py \
  --questions artifacts/schema_rag_test_questions.json \
  --index artifacts/schema_rag_index
```

## Code Conventions

### Python Style

- Use type hints for function signatures
- Use dataclasses for structured data (e.g., `GroundingResult`)
- Use `pathlib.Path` for file paths
- Follow standard Python naming conventions (snake_case for functions/variables, PascalCase for classes)
- Add docstrings for public methods

### Error Handling

- Raise `ImportError` for missing dependencies with helpful installation instructions
- Raise `FileNotFoundError` for missing required files
- Raise `RuntimeError` for service not initialized errors
- Use logging for warnings and debug information

### Testing

- Unit tests go in `tests/` directory
- Use pytest fixtures for test setup
- Mock external dependencies (faiss, SentenceTransformer) in unit tests
- Integration tests use `scripts/test_schema_rag_comprehensive.py`

## Core Classes and Functions

### `SchemaRagService` (schema_rag/service.py)

The main service class. Key methods:

- `__init__(index_path: Path)` - Initialize with path to index directory
- `retrieve_grounding(question: str, top_k: int = 5) -> GroundingResult` - Main query method
- `_expand_query_synonyms(question: str) -> str` - Expand query with synonyms
- `_extract_entities(question: str) -> Dict` - Extract program names, dates, filters
- `_lexical_boost(doc, keywords) -> float` - Calculate keyword-based score boost
- `_exact_match_boost(doc, keywords) -> float` - Boost for model+column matches
- `_recipe_pattern_boost(doc, question, entities) -> float` - Boost for recipe patterns
- `_penalize_incorrect_matches(doc, keywords, vector_score) -> float` - Penalty for bad matches

### `GroundingResult` (schema_rag/service.py)

Dataclass containing retrieval results:

```python
@dataclass
class GroundingResult:
    docs: List[Dict]         # Retrieved documents with scores
    schema_refs: List[Dict]  # Normalized schema references (model.table.column)
    join_hints: List[str]    # Join path strings
    recipes: List[Dict]      # Query recipe matches
    ambiguities: List[str]   # Semantic notes about ambiguities
```

## Document Types

The system uses three document types in the FAISS index:

1. **schema_model** - One per ORM model (table description, relationships)
2. **schema_column** - One per column (column description with aliases)
3. **query_recipe** - Template or curated query patterns with join hints

## Scoring System

Documents are ranked using a multi-component scoring system:

| Component | Score Range | Description |
|-----------|-------------|-------------|
| Vector Similarity | 0.0-1.0 | Base semantic similarity from FAISS |
| Lexical Boost | +2.0-4.0 | Keyword matches in metadata |
| Column Name Match | +3.0 | Query keyword matches column name |
| Model Name Match | +2.0 | Query keyword matches model name |
| Exact Match Boost | +6.0 | Both model and column match |
| Recipe Pattern Boost | +4.0-6.0 | Curated recipes + pattern matches |
| Entity Boost | +1.0-5.0 | Context-aware (program name, temporal) |
| Penalty | -2.0 to -3.0 | No matches with low vector score |

## Common Tasks

### Adding New Synonyms

Edit `schema_rag/schema_synonyms.json`:

```json
{
  "run": ["usage", "execution", "executed"],
  "how many times": ["usage_count", "count"]
}
```

Synonyms are bidirectional and support multi-word phrases (2-4 words).

### Modifying Scoring Weights

Edit the boost values in `schema_rag/service.py`:

- `_lexical_boost()` - Keyword matching weights
- `_exact_match_boost()` - Model+column match weight (+6.0)
- `_recipe_pattern_boost()` - Recipe and pattern weights
- `_penalize_incorrect_matches()` - Penalty values

### Adding New Test Cases

1. **Unit tests**: Add to `tests/test_service.py`
2. **Integration tests**: Add questions to `artifacts/schema_rag_test_questions.json`

### Changing the Embedding Model

Modify the model name in the index config or when building:

```bash
python scripts/build_schema_rag_index.py \
  --docs artifacts/schema_rag_docs.jsonl \
  --out artifacts/schema_rag_index/ \
  --model sentence-transformers/all-mpnet-base-v2
```

## Important Notes

1. **Index Rebuilding**: After modifying schema or documents, rebuild the FAISS index
2. **Backwards Compatibility**: Not a concern - refactor freely as needed
3. **Performance Baselines**: Current precision is 82.6% for model+column matching
4. **Test Reports**: Check `artifacts/SCHEMA_RAG_COMPREHENSIVE_TEST_REPORT.md` for detailed metrics
5. **Architecture Details**: See `docs/SCHEMA_RAG.md` for full architecture documentation

## Git Workflow

- Commit and push changes after each logical unit of work
- Run tests before committing: `pytest`
- Use descriptive commit messages explaining the "why"

## Troubleshooting

### "Required dependencies missing" Error

```bash
pip install faiss-cpu sentence-transformers
```

### "FAISS index not found" Error

Build the index first:

```bash
python scripts/build_schema_rag_index.py \
  --docs artifacts/schema_rag_docs.jsonl \
  --out artifacts/schema_rag_index/
```

### Low Retrieval Precision

1. Check synonym coverage in `schema_synonyms.json`
2. Review scoring weights in `service.py`
3. Consider adding curated recipes with higher boosts
4. Run comprehensive tests to identify failure patterns
