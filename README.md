# schema-rag

Schema-aware RAG (Retrieval Augmented Generation) service for retrieving database schema information using natural language queries.

## Overview

Schema RAG enables agents and LLMs to ground their responses in database schema information by:
- Embedding schema documentation (models, columns) and query recipes into a FAISS vector index
- Using hybrid retrieval (vector similarity + lexical matching) to find relevant schema information
- Returning structured references, join hints, and query recipes

**Performance:** Tested with 235 comprehensive questions across all 27 database models. Achieves **82.6% precision** for model+column matching with **100% query success rate**. See [Comprehensive Test Report](artifacts/SCHEMA_RAG_COMPREHENSIVE_TEST_REPORT.md) for detailed results.

## Features

- **Hybrid Retrieval**: Multi-component scoring system combining semantic vector search, lexical matching, exact match detection, and pattern recognition
- **High Precision**: Achieves 82.6% precision for model+column matching (95.7% for model matching) across 235 comprehensive test questions
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

First, you need a schema JSON file. You can:

- **For SQLAlchemy**: Export your models to JSON (see example export script)
- **For MSSQL Server**: Use the introspection script (see [MSSQL Server Support](#mssql-server-support) below)
- **For other databases**: Provide your own schema JSON in this format:

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
  --out artifacts/schema_rag_docs.jsonl \
  --dialect postgresql  # Options: postgresql, mysql, mssql, sqlite
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
- `scripts/introspect_mssql_schema.py`: Introspect MSSQL Server schema and export to JSON

## MSSQL Server Support

Schema RAG now supports MSSQL Server with dialect-specific SQL syntax in query recipes.

### Installation

Install a MSSQL driver (choose one):

```bash
# Option 1: pyodbc (recommended for Windows/Linux)
pip install pyodbc

# Option 2: pymssql (alternative)
pip install pymssql
```

**Note for Linux**: You may need to install the ODBC driver. On Ubuntu/Debian:
```bash
# Modern approach (Ubuntu 22.04+)
sudo mkdir -p /etc/apt/keyrings
curl https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/ubuntu/$(lsb_release -rs)/prod $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
ACCEPT_EULA=Y sudo apt-get install -y msodbcsql17
```

### Introspect MSSQL Schema

Connect to your MSSQL Server database and export the schema. The script supports secure password handling through multiple methods:

#### Option 1: Environment Variable (Recommended for Automation)

```bash
# Set password as environment variable (not visible in process listings)
export MSSQL_PASSWORD="your_password"

# Run without --password flag - script reads from MSSQL_PASSWORD
python scripts/introspect_mssql_schema.py \
  --server localhost \
  --database mydb \
  --username sa \
  --output artifacts/mssql_models.json
```

#### Option 2: Interactive Prompt (Recommended for Manual Use)

```bash
# Run without password - you will be prompted securely
python scripts/introspect_mssql_schema.py \
  --server localhost \
  --database mydb \
  --username sa \
  --output artifacts/mssql_models.json
# Enter MSSQL password: (input hidden)
```

#### Option 3: Password File (For Secure Automation)

```bash
# Create a password file with restricted permissions
echo "your_password" > ~/.mssql_password
chmod 600 ~/.mssql_password

# Use --password-file option
python scripts/introspect_mssql_schema.py \
  --server localhost \
  --database mydb \
  --username sa \
  --password-file ~/.mssql_password \
  --output artifacts/mssql_models.json
```

#### Option 4: Connection String via Environment Variable

```bash
# Set full connection string as environment variable
export MSSQL_CONNECTION_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=mydb;UID=sa;PWD=your_password"

# Run with just output path
python scripts/introspect_mssql_schema.py \
  --output artifacts/mssql_models.json
```

> **Security Note**: Avoid passing passwords directly on the command line (e.g., `--password mypassword`) as they may be visible in process listings (`ps aux`) and shell history.

### Generate Documents with MSSQL Dialect

When generating RAG documents, specify the `mssql` dialect to use MSSQL-specific SQL syntax in query recipes:

```bash
python scripts/generate_schema_rag_docs.py \
  --schema artifacts/mssql_models.json \
  --out artifacts/schema_rag_docs.jsonl \
  --dialect mssql
```

This will generate query recipes with MSSQL-specific functions:
- `GETDATE()` instead of `NOW()`
- `DATEADD(day, -N, GETDATE())` instead of `NOW() - INTERVAL N DAY` (where `N` is a number of days)
- `YEAR(column)` (same as other databases)

### Supported Dialects

The `--dialect` parameter supports:
- `postgresql` (default)
- `mysql`
- `mssql`
- `sqlite`

Each dialect uses appropriate SQL syntax in generated query recipes.

## Testing

### Comprehensive Test Results

The Schema RAG system has been thoroughly evaluated with **235 natural language questions** covering all 27 database models, advanced features, and edge cases. See the [Comprehensive Test Report](artifacts/SCHEMA_RAG_COMPREHENSIVE_TEST_REPORT.md) for detailed analysis.

**Overall Performance:**
- ✅ **100% query success rate** - All queries executed without errors
- ✅ **82.6% precision** for model+column matching (194/235 questions)
- ✅ **95.7% precision** for model matching (225/235 questions)
- ✅ **Rich context** - Average of 3.82 schema refs, 1.55 join hints, 3.35 recipes per query

**Category Performance Highlights:**
- **Assistant Features**: 100% accuracy (15/15)
- **Query Recipe Matching**: 93.3% accuracy (14/15)
- **Synonym Expansion**: 93.3% accuracy (14/15)
- **Advanced Features**: 90.0% accuracy (18/20)
- **Entity Extraction**: 86.7% accuracy (13/15)

**Test Reports:**
- [Comprehensive Test Report](artifacts/SCHEMA_RAG_COMPREHENSIVE_TEST_REPORT.md) - **Latest**: Full analysis of 235-question test suite
- [Test Suite Enhancement Summary](artifacts/TEST_SUITE_ENHANCEMENT_SUMMARY.md) - Details on test suite expansion
- [Original Test Report](artifacts/SCHEMA_RAG_TEST_REPORT.md) - Initial 110-question test results
- [Scoring Refinement Results](artifacts/SCORING_REFINEMENT_TEST_RESULTS.md) - Results after scoring improvements

**Run Tests:**
```bash
# Generate test questions
python scripts/test_schema_rag_comprehensive.py --generate-questions

# Run comprehensive test suite
python scripts/test_schema_rag_comprehensive.py \
  --questions artifacts/schema_rag_test_questions.json \
  --index artifacts/schema_rag_index \
  --output artifacts/schema_rag_test_results.json
```

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
