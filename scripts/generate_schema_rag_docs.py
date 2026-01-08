#!/usr/bin/env python3
"""Generate RAG documents from SQLAlchemy schema JSON.

This script generates three types of documents:
1. schema_model: One per ORM model
2. schema_column: One per column
3. query_recipe: Template-generated recipes for common query patterns
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List


def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text (column names, common terms)."""
    # Split on underscores and camelCase
    words = re.findall(r'[a-z]+|[A-Z][a-z]*', text.lower())
    # Add common aliases
    keywords = set(words)
    
    # Add common aliases for count columns
    if 'count' in text.lower():
        keywords.update(['count', 'number', 'total', 'quantity'])
    if 'success' in text.lower():
        keywords.update(['success', 'win', 'wins', 'succeeded'])
    if 'failure' in text.lower():
        keywords.update(['failure', 'fail', 'failed', 'error', 'errors'])
    if 'time' in text.lower():
        keywords.update(['time', 'duration', 'elapsed', 'runtime'])
    if 'usage' in text.lower():
        keywords.update(['usage', 'used', 'runs', 'executions'])
    
    return sorted(keywords)


def generate_column_text(column: Dict[str, Any], model: Dict[str, Any]) -> str:
    """Generate embedding text for a column document."""
    col_name = column["name"]
    col_type = column["type"]
    nullable = column.get("nullable", True)
    default = column.get("default")
    
    # Build natural language description
    parts = [f"Column: {model['model']}.{col_name}"]
    parts.append(f"(table {model['table']})")
    
    # Type description
    type_desc = col_type.lower()
    if "integer" in type_desc:
        type_desc = "integer"
    elif "string" in type_desc or "text" in type_desc:
        type_desc = "text"
    elif "float" in type_desc or "numeric" in type_desc:
        type_desc = "numeric"
    elif "datetime" in type_desc:
        type_desc = "datetime"
    elif "json" in type_desc:
        type_desc = "JSON object"
    
    parts.append(f"— {type_desc}")
    
    # Add semantic description based on column name
    if col_name.endswith("_count"):
        base_name = col_name[:-6]  # Remove "_count"
        parts.append(f"counter of {base_name.replace('_', ' ')}")
    elif col_name.endswith("_id"):
        parts.append("foreign key identifier")
    elif "time" in col_name.lower():
        parts.append("timestamp or duration")
    elif "name" in col_name.lower():
        parts.append("name or label")
    elif "description" in col_name.lower():
        parts.append("descriptive text")
    
    if not nullable:
        parts.append("Required field.")
    if default:
        # Format function defaults more clearly
        if default in ["generate_uuid", "utc_now", "dict", "list"]:
            parts.append(f"Default: function {default}.")
        else:
            parts.append(f"Default: {default}.")
    
    # Add join hints if foreign key
    if "foreign_keys" in column:
        for fk in column["foreign_keys"]:
            if fk.get("target_table") and fk.get("target_column"):
                parts.append(
                    f"Typically filtered by join {model['table']}.{col_name} -> "
                    f"{fk['target_table']}.{fk['target_column']}"
                )
    
    # Add related columns from same model
    related = []
    if "count" in col_name.lower():
        # Look for other count columns
        for other_col in model["columns"]:
            if other_col["name"] != col_name and "count" in other_col["name"].lower():
                related.append(other_col["name"])
    if related:
        parts.append(f"Related columns: {', '.join(related)}")
    
    return " ".join(parts)


def generate_model_text(model: Dict[str, Any]) -> str:
    """Generate embedding text for a model document."""
    parts = [f"Model: {model['model']}"]
    parts.append(f"(table {model['table']})")
    
    if model.get("docstring"):
        parts.append(f"— {model['docstring'].strip()}")
    
    # Add relationship info
    if model.get("relationships"):
        rel_names = [r["name"] for r in model["relationships"]]
        if rel_names:
            parts.append(f"Relationships: {', '.join(rel_names)}")
    
    return " ".join(parts)


def generate_query_recipe(
    model: Dict[str, Any],
    column: Dict[str, Any],
    target_model: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Generate a query recipe for accessing a column via joins."""
    recipe_id = f"query_recipe:{model['table']}.{column['name']}"
    
    # Determine if this needs a join
    needs_join = False
    join_hints = []
    
    if "foreign_keys" in column:
        for fk in column["foreign_keys"]:
            if fk.get("target_table"):
                needs_join = True
                join_hints.append(
                    f"{model['table']}.{column['name']} -> {fk['target_table']}.{fk['target_column']}"
                )
    
    # Check relationships for reverse joins
    if model.get("relationships"):
        for rel in model["relationships"]:
            if rel.get("join_pairs"):
                for pair in rel["join_pairs"]:
                    join_hints.append(
                        f"{model['table']}.{pair['local_column']} -> "
                        f"{pair['remote_table']}.{pair['remote_column']}"
                    )
    
    # Generate recipe text
    text_parts = [f"Recipe: access {column['name']} from {model['table']}"]
    
    if needs_join:
        text_parts.append("Join required:")
        for hint in join_hints:
            text_parts.append(f"- {hint}")
    
    # Add filter hints
    if "name" in column["name"].lower() or "id" in column["name"].lower():
        text_parts.append(f"Filter by {model['table']}.{column['name']} to find specific records.")
    
    # Add return hint
    text_parts.append(f"Return {model['model']}.{column['name']}")
    
    # Add semantics notes for variant_id case
    if column["name"] == "variant_id" and model["table"] == "program_statistics":
        text_parts.append(
            "Note: If multiple rows exist due to variants (variant_id), either sum across rows "
            "or choose variant_id IS NULL depending on requested semantics."
        )
    
    return {
        "id": recipe_id,
        "doc_type": "query_recipe",
        "text": ". ".join(text_parts),
        "metadata": {
            "model": model["model"],
            "table": model["table"],
            "column": column["name"],
            "join_hints": join_hints,
            "keywords": extract_keywords(column["name"]),
            "semantics": "variant_id handling" if column["name"] == "variant_id" else None,
        },
    }


def generate_documents(schema_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate all RAG documents from schema data."""
    documents = []
    models = schema_data.get("models", [])
    
    for model in models:
        # 1. Generate schema_model document
        model_doc = {
            "id": f"schema_model:{model['module']}.{model['model']}",
            "doc_type": "schema_model",
            "text": generate_model_text(model),
            "metadata": {
                "model": model["model"],
                "table": model["table"],
                "source_file": model.get("source_file", "unknown"),
            },
        }
        documents.append(model_doc)
        
        # 2. Generate schema_column documents
        for column in model["columns"]:
            col_doc = {
                "id": f"schema_column:{model['module']}.{model['model']}.{column['name']}",
                "doc_type": "schema_column",
                "text": generate_column_text(column, model),
                "metadata": {
                    "model": model["model"],
                    "table": model["table"],
                    "column": column["name"],
                    "type": column["type"],
                    "nullable": column.get("nullable", True),
                    "source_file": model.get("source_file", "unknown"),
                    "keywords": extract_keywords(column["name"]),
                },
            }
            documents.append(col_doc)
            
            # 3. Generate query_recipe for columns that might need joins
            # Generate recipes for foreign keys and important columns
            if (
                "foreign_keys" in column
                or column["name"].endswith("_count")
                or "name" in column["name"].lower()
                or "id" in column["name"].lower()
            ):
                recipe = generate_query_recipe(model, column)
                documents.append(recipe)
    
    # Generate special recipes for common patterns
    # Recipe: success count for program name
    program_model = next((m for m in models if m["table"] == "programs"), None)
    stats_model = next((m for m in models if m["table"] == "program_statistics"), None)
    
    if program_model and stats_model:
        success_col = next(
            (c for c in stats_model["columns"] if c["name"] == "success_count"), None
        )
        if success_col:
            recipe = {
                "id": "query_recipe:success_count_for_program_name",
                "doc_type": "query_recipe",
                "text": (
                    "Recipe: success count for a named program. "
                    "Join programs to program_statistics on programs.id = program_statistics.program_id. "
                    "Filter programs.name by the user's program name. "
                    "Return program_statistics.success_count. "
                    "If multiple rows exist due to variants (variant_id), either sum across rows "
                    "or choose variant_id IS NULL depending on requested semantics."
                ),
                "metadata": {
                    "model": "ProgramStatistics",
                    "table": "program_statistics",
                    "column": "success_count",
                    "join_hints": [
                        "program_statistics.program_id -> programs.id",
                        "programs.name (filter by user's program name)",
                    ],
                    "keywords": ["success", "count", "program", "name"],
                    "semantics": "variant_id may require sum vs base-only",
                },
            }
            documents.append(recipe)
    
    return documents


def load_curated_recipes(curated_path: Path) -> List[Dict[str, Any]]:
    """Load curated recipes from JSONL file if it exists."""
    if not curated_path.exists():
        return []
    
    recipes = []
    try:
        with open(curated_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    recipes.append(json.loads(line))
        print(f"Loaded {len(recipes)} curated recipes from {curated_path}")
    except Exception as exc:
        print(f"Warning: Failed to load curated recipes: {exc}")
        return []
    
    return recipes


def merge_curated_recipes(documents: List[Dict[str, Any]], curated_recipes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge curated recipes into documents, with curated taking precedence."""
    # Create a map of document IDs
    doc_ids = {doc["id"]: i for i, doc in enumerate(documents)}
    
    # Add curated recipes, replacing generated ones if ID conflicts
    for curated_recipe in curated_recipes:
        recipe_id = curated_recipe.get("id")
        if recipe_id in doc_ids:
            # Replace existing recipe with curated one
            documents[doc_ids[recipe_id]] = curated_recipe
            print(f"  Replaced recipe: {recipe_id}")
        else:
            # Add new curated recipe
            documents.append(curated_recipe)
            print(f"  Added curated recipe: {recipe_id}")
    
    return documents


def main():
    parser = argparse.ArgumentParser(description="Generate RAG documents from schema JSON")
    parser.add_argument(
        "--schema",
        type=str,
        required=True,
        help="Input schema JSON file path",
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output JSONL file path",
    )
    parser.add_argument(
        "--curated",
        type=str,
        default="artifacts/schema_rag_curated_recipes.jsonl",
        help="Path to curated recipes JSONL file (optional)",
    )
    args = parser.parse_args()
    
    schema_path = Path(args.schema)
    output_path = Path(args.out)
    curated_path = Path(args.curated)
    
    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}")
        return 1
    
    print(f"Loading schema from {schema_path}...")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_data = json.load(f)
    
    print("Generating documents...")
    documents = generate_documents(schema_data)
    
    # Load and merge curated recipes
    curated_recipes = load_curated_recipes(curated_path)
    if curated_recipes:
        print("Merging curated recipes...")
        documents = merge_curated_recipes(documents, curated_recipes)
    
    print(f"Writing {len(documents)} documents to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for doc in documents:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    
    print(f"✓ Generated {len(documents)} documents")
    
    # Print summary
    doc_types = {}
    for doc in documents:
        doc_type = doc["doc_type"]
        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
    
    print("\nDocument summary:")
    for doc_type, count in sorted(doc_types.items()):
        print(f"  {doc_type}: {count}")
    
    return 0


if __name__ == "__main__":
    exit(main())
