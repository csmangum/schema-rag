# Schema RAG Unit Tests

Comprehensive unit tests for the `SchemaRagService` class.

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test class
pytest tests/test_service.py::TestSchemaRagServiceInitialization -v

# Run specific test
pytest tests/test_service.py::TestSchemaRagServiceInitialization::test_init_success -v
```

## Test Coverage

The test suite includes 37 unit tests covering:

### Initialization Tests (5 tests)
- Missing dependencies handling
- Missing index file handling
- Missing docs file handling
- Missing config file handling
- Successful initialization

### Query Expansion Tests (3 tests)
- No synonyms file handling
- Synonym expansion
- Synonym load error handling

### Keyword Extraction Tests (4 tests)
- Simple keyword extraction
- CamelCase handling
- Underscore handling
- Deduplication

### Lexical Boosting Tests (4 tests)
- Keyword match boosting
- Column name match boosting
- Model name match boosting
- No matches handling

### Entity Extraction Tests (8 tests)
- Program name extraction
- Date extraction (various patterns)
- Minimum value extraction
- Maximum value extraction
- Comparison operators (>, <, =)
- No entities handling

### Entity Boosting Tests (4 tests)
- Program name boosting
- Date column boosting
- Numeric column boosting
- No entities handling

### Retrieve Grounding Tests (6 tests)
- Successful retrieval
- Recipe inclusion
- Top-k parameter
- Not initialized error
- Join hint deduplication
- Ambiguity extraction

### GroundingResult Tests (2 tests)
- Result creation
- Empty result handling

## Test Structure

Tests use pytest fixtures to create isolated service instances with mocked dependencies (FAISS, SentenceTransformer) to avoid requiring actual index files.

## Dependencies

Tests require:
- pytest>=7.0.0
- pytest-cov>=4.0.0 (optional, for coverage reports)

Install with:
```bash
pip install -r requirements.txt
```
