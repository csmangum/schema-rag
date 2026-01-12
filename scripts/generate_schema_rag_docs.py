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


# SQL Dialect Support
SQL_DIALECTS = {
    "postgresql": {
        "current_timestamp": "NOW()",
        "date_subtract": "NOW() - INTERVAL {days} DAY",
        "date_subtract_alt": "date_sub(NOW(), INTERVAL {days} DAY)",
        "year_function": "YEAR({column})",
    },
    "mysql": {
        "current_timestamp": "NOW()",
        "date_subtract": "NOW() - INTERVAL {days} DAY",
        "date_subtract_alt": "date_sub(NOW(), INTERVAL {days} DAY)",
        "year_function": "YEAR({column})",
    },
    "mssql": {
        "current_timestamp": "GETDATE()",
        "date_subtract": "DATEADD(day, -{days}, GETDATE())",
        "date_subtract_alt": "DATEADD(day, -{days}, GETDATE())",
        "year_function": "YEAR({column})",
    },
    "sqlite": {
        "current_timestamp": "datetime('now')",
        "date_subtract": "datetime('now', '-{days} days')",
        "date_subtract_alt": "datetime('now', '-{days} days')",
        "year_function": "strftime('%Y', {column})",
    },
}


def get_sql_function(dialect: str, function_name: str, **kwargs) -> str:
    """Get dialect-specific SQL function.
    
    Args:
        dialect: Database dialect (postgresql, mysql, mssql, sqlite)
        function_name: Name of the function template
        **kwargs: Parameters to format into the template
        
    Returns:
        Formatted SQL function string
    """
    dialect_lower = dialect.lower()
    if dialect_lower not in SQL_DIALECTS:
        # Default to postgresql if unknown dialect
        dialect_lower = "postgresql"
    
    template = SQL_DIALECTS[dialect_lower].get(function_name, "")
    if not template:
        # Fallback to postgresql
        template = SQL_DIALECTS["postgresql"].get(function_name, "")
    
    return template.format(**kwargs)


def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text (column names, common terms)."""
    # Split on underscores and camelCase
    words = re.findall(r'[a-z]+|[A-Z][a-z]*', text.lower())
    # Add common aliases
    keywords = set(words)
    
    # Add common aliases for count columns
    if 'count' in text.lower():
        keywords.update(['count', 'number', 'total', 'quantity', 'how many', 'how many times'])
    if 'success' in text.lower():
        keywords.update(['success', 'win', 'wins', 'succeeded'])
    if 'failure' in text.lower():
        keywords.update(['failure', 'fail', 'failed', 'error', 'errors'])
    if 'time' in text.lower():
        keywords.update(['time', 'duration', 'elapsed', 'runtime'])
    if 'usage' in text.lower():
        keywords.update(['usage', 'used', 'runs', 'executions', 'run', 'ran'])
    if 'created' in text.lower() or 'created_at' in text.lower():
        keywords.update(['created', 'creation', 'started', 'begin', 'new'])
    if 'updated' in text.lower() or 'updated_at' in text.lower():
        keywords.update(['updated', 'update', 'modified', 'changed', 'recently', 'recent'])
    if 'started' in text.lower() or 'started_at' in text.lower():
        keywords.update(['started', 'start', 'begin', 'began', 'initiated'])
    if 'completed' in text.lower() or 'completed_at' in text.lower():
        keywords.update(['completed', 'complete', 'finished', 'done', 'ended'])
    if 'status' in text.lower():
        keywords.update(['status', 'state', 'condition', 'running', 'completed', 'active', 'failed'])
    if 'name' in text.lower():
        keywords.update(['name', 'names', 'title', 'titles', 'label', 'labels'])
    if 'description' in text.lower():
        keywords.update(['description', 'descriptions', 'detail', 'details', 'info', 'information'])
    if 'related' in text.lower() or 'link' in text.lower():
        keywords.update(['related', 'link', 'links', 'linked', 'connection', 'connections', 'associated'])
    
    return sorted(keywords)


def get_key_columns(model: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract key columns from a model (count columns, name columns, status columns, foreign keys)."""
    key_cols = []
    for col in model.get("columns", []):
        col_name = col["name"].lower()
        if (
            col_name.endswith("_count")
            or "name" in col_name
            or "status" in col_name
            or "state" in col_name
            or col_name.endswith("_id")
            or "created_at" in col_name
            or "updated_at" in col_name
        ):
            key_cols.append(col)
    return key_cols


def describe_column_purpose(column: Dict[str, Any], model: Dict[str, Any]) -> str:
    """Generate a natural language description of a column's purpose."""
    col_name = column["name"]
    col_name_lower = col_name.lower()
    
    descriptions = []
    
    if col_name.endswith("_count"):
        base_name = col_name[:-6].replace("_", " ")
        descriptions.append(f"number of {base_name}")
    elif col_name.endswith("_id"):
        if "foreign_keys" in column:
            for fk in column["foreign_keys"]:
                target_table = fk.get("target_table", "").replace("_", " ")
                descriptions.append(f"identifier linking to {target_table}")
        else:
            descriptions.append("identifier")
    elif "name" in col_name_lower:
        descriptions.append("name or label for identification")
    elif "description" in col_name_lower:
        descriptions.append("descriptive text or details")
    elif "status" in col_name_lower or "state" in col_name_lower:
        descriptions.append("current status or state")
    elif "created_at" in col_name_lower:
        descriptions.append("timestamp when record was created")
    elif "updated_at" in col_name_lower:
        descriptions.append("timestamp when record was last updated")
    elif "time" in col_name_lower:
        if "avg" in col_name_lower or "average" in col_name_lower:
            descriptions.append("average execution or processing time")
        else:
            descriptions.append("timestamp or duration")
    elif "success" in col_name_lower:
        descriptions.append("number of successful operations")
    elif "failure" in col_name_lower:
        descriptions.append("number of failed operations")
    elif "usage" in col_name_lower:
        descriptions.append("usage count or frequency")
    
    return descriptions[0] if descriptions else "data field"


def get_example_queries_for_model(model: Dict[str, Any]) -> List[str]:
    """Generate example natural language queries that would match this model."""
    model_name = model["model"]
    model_name_lower = model_name.lower().replace("_", " ")
    
    examples = []
    
    # Find key columns
    name_col = next((c for c in model["columns"] if "name" in c["name"].lower()), None)
    count_cols = [c for c in model["columns"] if c["name"].endswith("_count")]
    status_col = next((c for c in model["columns"] if "status" in c["name"].lower() or "state" in c["name"].lower()), None)
    
    # Generate examples based on model type and columns
    if "statistics" in model_name_lower or "stats" in model_name_lower:
        if name_col:
            examples.append(f"{model_name_lower} for {name_col['name'].replace('_', ' ')}")
        if count_cols:
            for col in count_cols[:2]:  # Limit to first 2
                base = col["name"].replace("_count", "").replace("_", " ")
                examples.append(f"{base} count for {model_name_lower.replace('statistics', '').strip()}")
                examples.append(f"how many {base} for {model_name_lower.replace('statistics', '').strip()}")
    elif "program" in model_name_lower:
        examples.append(f"{model_name_lower} information")
        examples.append(f"{model_name_lower} details")
        if name_col:
            examples.append(f"list all {model_name_lower} names")
    elif "simulation" in model_name_lower:
        examples.append(f"{model_name_lower} status")
        examples.append(f"{model_name_lower} information")
        if status_col:
            examples.append(f"running {model_name_lower}s")
            examples.append(f"completed {model_name_lower}s")
    elif "experiment" in model_name_lower:
        examples.append(f"{model_name_lower} details")
        examples.append(f"{model_name_lower} information")
    elif "research" in model_name_lower:
        examples.append(f"{model_name_lower} goals")
        examples.append(f"{model_name_lower} questions")
    elif "message" in model_name_lower or "chat" in model_name_lower:
        examples.append(f"{model_name_lower} history")
        examples.append(f"{model_name_lower} content")
    elif "rating" in model_name_lower:
        examples.append(f"{model_name_lower}s")
        examples.append(f"user {model_name_lower}s")
    elif "session" in model_name_lower:
        examples.append(f"{model_name_lower} information")
        examples.append(f"active {model_name_lower}s")
    
    # Generic examples
    if name_col:
        examples.append(f"{model_name_lower} names")
    if status_col:
        examples.append(f"{model_name_lower} status")
    
    return examples[:5]  # Limit to 5 examples


def get_common_use_cases(model: Dict[str, Any]) -> List[str]:
    """Identify common use cases for a model based on its columns and name."""
    model_name = model["model"]
    model_name_lower = model_name.lower()
    use_cases = []
    
    # Analyze columns to determine use cases
    has_count_cols = any(c["name"].endswith("_count") for c in model["columns"])
    has_status = any("status" in c["name"].lower() or "state" in c["name"].lower() for c in model["columns"])
    has_timestamps = any("created_at" in c["name"].lower() or "updated_at" in c["name"].lower() for c in model["columns"])
    has_name = any("name" in c["name"].lower() for c in model["columns"])
    
    if "statistics" in model_name_lower or "stats" in model_name_lower:
        use_cases.append("performance metrics and analytics")
        use_cases.append("aggregated execution statistics")
        if has_count_cols:
            use_cases.append("success and failure tracking")
    elif "program" in model_name_lower:
        use_cases.append("program definitions and metadata")
        if has_name:
            use_cases.append("program identification and lookup")
    elif "simulation" in model_name_lower:
        use_cases.append("simulation execution tracking")
        if has_status:
            use_cases.append("simulation status monitoring")
    elif "experiment" in model_name_lower:
        use_cases.append("experiment management and tracking")
    elif "research" in model_name_lower:
        use_cases.append("research goals and questions")
    elif "message" in model_name_lower or "chat" in model_name_lower:
        use_cases.append("conversation history")
        use_cases.append("message content retrieval")
    elif "rating" in model_name_lower:
        use_cases.append("user feedback and ratings")
    elif "session" in model_name_lower:
        use_cases.append("user session management")
    
    if has_timestamps:
        use_cases.append("temporal queries and filtering")
    
    return use_cases[:4]  # Limit to 4 use cases


def get_column_query_patterns(column: Dict[str, Any], model: Dict[str, Any]) -> List[str]:
    """Generate common query patterns for a column."""
    col_name = column["name"]
    col_name_lower = col_name.lower()
    col_type = column["type"].lower()
    table_name = model["table"]
    patterns = []
    
    if col_name.endswith("_count"):
        patterns.append(f"COUNT(*) or SUM({col_name}) for aggregation")
        patterns.append(f"WHERE {col_name} > value for filtering")
    elif "status" in col_name_lower or "state" in col_name_lower:
        patterns.append(f"WHERE {col_name} = 'status_value' for filtering")
        patterns.append(f"COUNT(*) WHERE {col_name} = 'status' for counting by status")
    elif "created_at" in col_name_lower or "updated_at" in col_name_lower:
        patterns.append(f"WHERE {col_name} >= date for temporal filtering")
        patterns.append(f"ORDER BY {col_name} DESC for recent records")
    elif "datetime" in col_type or "date" in col_type:
        patterns.append(f"WHERE YEAR({col_name}) = year for year filtering")
        patterns.append(f"WHERE {col_name} BETWEEN start AND end for date ranges")
    elif "integer" in col_type or "float" in col_type or "numeric" in col_type:
        if "avg" in col_name_lower or "average" in col_name_lower:
            patterns.append(f"AVG({col_name}) for average calculation")
        else:
            patterns.append(f"MAX({col_name}) or MIN({col_name}) for min/max")
            patterns.append(f"WHERE {col_name} > value for numeric filtering")
    elif "name" in col_name_lower:
        patterns.append(f"WHERE {col_name} = 'value' for exact match")
        patterns.append(f"WHERE {col_name} LIKE 'pattern%' for pattern matching")
    elif col_name.endswith("_id") and "foreign_keys" in column:
        patterns.append(f"JOIN {table_name}.{col_name} -> target_table.id for relationships")
    
    return patterns[:3]  # Limit to 3 patterns


def get_status_example_values(column: Dict[str, Any]) -> List[str]:
    """Get example status values for status/state columns."""
    col_name = column["name"].lower()
    
    # Common status values based on column name
    if "simulation" in col_name or "execution" in col_name:
        return ["running", "completed", "failed", "pending"]
    elif "program" in col_name:
        return ["active", "inactive", "archived"]
    elif "experiment" in col_name:
        return ["draft", "running", "completed", "cancelled"]
    else:
        return ["active", "inactive", "pending", "completed", "failed"]


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
    
    # Add usage context
    purpose = describe_column_purpose(column, model)
    if purpose:
        parts.append(f"Used to track or store {purpose}.")
    
    if not nullable:
        parts.append("Required field.")
    if default:
        # Format function defaults more clearly
        if default in ["generate_uuid", "utc_now", "dict", "list"]:
            parts.append(f"Default: function {default}.")
        else:
            parts.append(f"Default: {default}.")
    
    # Add example values for status/state columns
    if "status" in col_name.lower() or "state" in col_name.lower():
        example_values = get_status_example_values(column)
        if example_values:
            parts.append(f"Example values: {', '.join(repr(v) for v in example_values)}.")
    
    # Add relationship context for foreign keys
    if "foreign_keys" in column:
        for fk in column["foreign_keys"]:
            if fk.get("target_table") and fk.get("target_column"):
                target_table = fk["target_table"].replace("_", " ")
                parts.append(
                    f"Links to {target_table} table via {fk['target_column']} to establish relationship."
                )
                parts.append(
                    f"Join pattern: {model['table']}.{col_name} -> "
                    f"{fk['target_table']}.{fk['target_column']}"
                )
    
    # Add query patterns
    query_patterns = get_column_query_patterns(column, model)
    if query_patterns:
        parts.append(f"Common query patterns: {', '.join(query_patterns)}.")
    
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
    
    # Add model purpose/context
    model_name_lower = model["model"].lower()
    if "statistics" in model_name_lower or "stats" in model_name_lower:
        parts.append("This model stores aggregated performance metrics and execution statistics.")
    elif "program" in model_name_lower:
        parts.append("This model represents executable simulation programs and their metadata.")
    elif "simulation" in model_name_lower:
        parts.append("This model tracks simulation executions, status, and results.")
    elif "experiment" in model_name_lower:
        parts.append("This model manages experiments and their configurations.")
    elif "research" in model_name_lower:
        parts.append("This model stores research goals, questions, and related information.")
    elif "message" in model_name_lower or "chat" in model_name_lower:
        parts.append("This model stores conversation history and message content.")
    elif "rating" in model_name_lower:
        parts.append("This model stores user ratings and feedback.")
    elif "session" in model_name_lower:
        parts.append("This model manages user sessions and authentication.")
    
    # Add column summary (key columns and their purposes)
    key_cols = get_key_columns(model)
    if key_cols:
        col_descriptions = []
        for col in key_cols[:6]:  # Limit to 6 key columns
            purpose = describe_column_purpose(col, model)
            col_display = col["name"].replace("_", " ")
            col_descriptions.append(f"{col_display} ({purpose})")
        if col_descriptions:
            parts.append(f"Key columns: {', '.join(col_descriptions)}")
    
    # Add common use cases
    use_cases = get_common_use_cases(model)
    if use_cases:
        parts.append(f"Commonly used for: {', '.join(use_cases)}")
    
    # Add example queries
    example_queries = get_example_queries_for_model(model)
    if example_queries:
        parts.append(f"Example queries: {', '.join(repr(q) for q in example_queries)}")
    
    # Add relationship context
    if model.get("relationships"):
        rel_descriptions = []
        for rel in model["relationships"]:
            rel_name = rel.get("name", "")
            target_model = rel.get("target_model", "")
            join_pairs = rel.get("join_pairs", [])
            
            if target_model and join_pairs:
                # Describe the relationship
                target_display = target_model.lower().replace("_", " ")
                rel_descriptions.append(f"related to {target_display} via {rel_name}")
        
        if rel_descriptions:
            parts.append(f"Relationships: {', '.join(rel_descriptions)}")
    
    # Add foreign key relationships context
    fk_descriptions = []
    for col in model.get("columns", []):
        if "foreign_keys" in col:
            for fk in col["foreign_keys"]:
                target_table = fk.get("target_table", "")
                target_column = fk.get("target_column", "")
                if target_table:
                    target_display = target_table.replace("_", " ")
                    fk_descriptions.append(
                        f"linked to {target_display} via {col['name']} -> {target_column}"
                    )
    
    if fk_descriptions:
        parts.append(f"Foreign key relationships: {', '.join(fk_descriptions[:3])}")  # Limit to 3
    
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


def generate_relationship_recipes(
    model: Dict[str, Any],
    all_models: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate recipes for relationship queries."""
    recipes = []
    
    if not model.get("relationships"):
        return recipes
    
    model_name_lower = model["model"].lower()
    table_name = model["table"]
    
    for rel in model["relationships"]:
        rel_name = rel.get("name", "")
        target_table = rel.get("target_table", "")
        target_model_name = rel.get("target_model", "")
        join_pairs = rel.get("join_pairs", [])
        
        if not join_pairs:
            continue
        
        # Find target model
        target_model = next((m for m in all_models if m["table"] == target_table), None)
        if not target_model:
            continue
        
        # Generate recipe for forward relationship
        join_hints = []
        for pair in join_pairs:
            remote_table = pair.get('remote_table', target_table)
            join_hints.append(
                f"{table_name}.{pair['local_column']} -> {remote_table}.{pair['remote_column']}"
            )
        
        # Recipe: "X linked to Y" or "X related to Y"
        recipe_id = f"query_recipe:{table_name}_linked_to_{target_table}"
        text_parts = [
            f"Recipe: {model_name_lower} linked to {target_model_name.lower()}. "
            f"Join {table_name} to {target_table} on {join_hints[0] if join_hints else 'appropriate foreign key'}. "
            f"Filter by {table_name} fields to find specific records. "
            f"Return related {target_table} records or {target_table} fields."
        ]
        
        keywords = extract_keywords(f"{rel_name} {target_model_name}")
        keywords.extend(["linked", "related", "connection", "relationship"])
        
        recipes.append({
            "id": recipe_id,
            "doc_type": "query_recipe",
            "text": ". ".join(text_parts),
            "metadata": {
                "model": model["model"],
                "table": table_name,
                "column": None,
                "join_hints": join_hints,
                "keywords": sorted(set(keywords)),
                "semantics": None,
                "recipe_type": "relationship",
            },
        })
        
        # Generate recipe for reverse relationship (e.g., "experiments for research")
        reverse_recipe_id = f"query_recipe:{target_table}_for_{table_name}"
        reverse_text_parts = [
            f"Recipe: {target_model_name.lower()} for {model_name_lower}. "
            f"Join {target_table} to {table_name} on {join_hints[0] if join_hints else 'appropriate foreign key'}. "
            f"Filter by {table_name} fields to find specific {model_name_lower}. "
            f"Return related {target_table} records."
        ]
        
        reverse_keywords = extract_keywords(f"{target_model_name} {model_name_lower}")
        reverse_keywords.extend(["for", "belongs", "associated"])
        
        recipes.append({
            "id": reverse_recipe_id,
            "doc_type": "query_recipe",
            "text": ". ".join(reverse_text_parts),
            "metadata": {
                "model": target_model_name,
                "table": target_table,
                "column": None,
                "join_hints": join_hints,
                "keywords": sorted(set(reverse_keywords)),
                "semantics": None,
                "recipe_type": "relationship",
            },
        })
    
    return recipes


def generate_aggregation_recipes(
    model: Dict[str, Any],
    column: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate recipes for aggregation queries."""
    recipes = []
    col_name = column["name"]
    col_type = column["type"].lower()
    table_name = model["table"]
    model_name = model["model"]
    
    # Count columns
    if col_name.endswith("_count") or "count" in col_name.lower():
        # "How many" queries
        recipe_id = f"query_recipe:how_many_{col_name}"
        text_parts = [
            f"Recipe: how many {col_name.replace('_count', '').replace('_', ' ')}. "
            f"Query {table_name} table. "
            f"Use COUNT(*) or SUM({col_name}) depending on semantics. "
            f"Filter by appropriate conditions if specified. "
            f"Return the count as a number."
        ]
        
        keywords = extract_keywords(col_name)
        keywords.extend(["how many", "count", "number", "total", "quantity"])
        
        recipes.append({
            "id": recipe_id,
            "doc_type": "query_recipe",
            "text": ". ".join(text_parts),
            "metadata": {
                "model": model_name,
                "table": table_name,
                "column": col_name,
                "join_hints": [],
                "keywords": sorted(set(keywords)),
                "semantics": "Aggregation: COUNT or SUM",
                "recipe_type": "aggregation",
            },
        })
    
    # Numeric columns for aggregation
    if "integer" in col_type or "float" in col_type or "numeric" in col_type:
        if col_name.endswith("_count"):
            return recipes  # Already handled above
        
        # Average queries
        if "avg" in col_name.lower() or "average" in col_name.lower():
            recipe_id = f"query_recipe:average_{col_name}"
            text_parts = [
                f"Recipe: average {col_name.replace('_', ' ')}. "
                f"Query {table_name} table. "
                f"Use AVG({col_name}) to calculate average. "
                f"Filter by appropriate conditions if specified. "
                f"Group by relevant fields if needed. "
                f"Return the average value."
            ]
            
            keywords = extract_keywords(col_name)
            keywords.extend(["average", "avg", "mean", "typical"])
            
            recipes.append({
                "id": recipe_id,
                "doc_type": "query_recipe",
                "text": ". ".join(text_parts),
                "metadata": {
                    "model": model_name,
                    "table": table_name,
                    "column": col_name,
                    "join_hints": [],
                    "keywords": sorted(set(keywords)),
                    "semantics": "Aggregation: AVG",
                    "recipe_type": "aggregation",
                },
            })
        
        # Maximum queries
        recipe_id = f"query_recipe:maximum_{col_name}"
        text_parts = [
            f"Recipe: maximum or highest {col_name.replace('_', ' ')}. "
            f"Query {table_name} table. "
            f"Use MAX({col_name}) to find maximum value. "
            f"Or use ORDER BY {col_name} DESC LIMIT 1 to find record with highest value. "
            f"Filter by appropriate conditions if specified. "
            f"Return the maximum value or the record with maximum value."
        ]
        
        keywords = extract_keywords(col_name)
        keywords.extend(["maximum", "max", "highest", "top", "best", "most"])
        
        recipes.append({
            "id": recipe_id,
            "doc_type": "query_recipe",
            "text": ". ".join(text_parts),
            "metadata": {
                "model": model_name,
                "table": table_name,
                "column": col_name,
                "join_hints": [],
                "keywords": sorted(set(keywords)),
                "semantics": "Aggregation: MAX",
                "recipe_type": "aggregation",
            },
        })
        
        # Minimum queries
        recipe_id = f"query_recipe:minimum_{col_name}"
        text_parts = [
            f"Recipe: minimum or lowest {col_name.replace('_', ' ')}. "
            f"Query {table_name} table. "
            f"Use MIN({col_name}) to find minimum value. "
            f"Or use ORDER BY {col_name} ASC LIMIT 1 to find record with lowest value. "
            f"Filter by appropriate conditions if specified. "
            f"Return the minimum value or the record with minimum value."
        ]
        
        keywords = extract_keywords(col_name)
        keywords.extend(["minimum", "min", "lowest", "least", "smallest"])
        
        recipes.append({
            "id": recipe_id,
            "doc_type": "query_recipe",
            "text": ". ".join(text_parts),
            "metadata": {
                "model": model_name,
                "table": table_name,
                "column": col_name,
                "join_hints": [],
                "keywords": sorted(set(keywords)),
                "semantics": "Aggregation: MIN",
                "recipe_type": "aggregation",
            },
        })
    
    return recipes


def generate_temporal_recipes(
    model: Dict[str, Any],
    column: Dict[str, Any],
    dialect: str = "postgresql",
) -> List[Dict[str, Any]]:
    """Generate recipes for temporal/date-time queries.
    
    Args:
        model: Model dictionary
        column: Column dictionary
        dialect: Database dialect (postgresql, mysql, mssql, sqlite)
    """
    recipes = []
    col_name = column["name"]
    col_type = column["type"].lower()
    table_name = model["table"]
    model_name = model["model"]
    
    if "datetime" not in col_type and "date" not in col_type:
        return recipes
    
    # Get dialect-specific SQL functions
    year_func = get_sql_function(dialect, "year_function", column=col_name)
    date_subtract_n = get_sql_function(dialect, "date_subtract", days="N")
    date_subtract_7 = get_sql_function(dialect, "date_subtract", days=7)
    date_subtract_alt = get_sql_function(dialect, "date_subtract_alt", days="N")
    date_subtract_alt_7 = get_sql_function(dialect, "date_subtract_alt", days=7)
    
    # "Created in" or "Started in" queries
    if "created" in col_name.lower() or "started" in col_name.lower():
        recipe_id = f"query_recipe:{col_name}_in_year"
        text_parts = [
            f"Recipe: {model_name.lower()} {col_name.replace('_', ' ')} in specific year or date range. "
            f"Query {table_name} table. "
            f"Filter by {col_name} using date functions: WHERE {year_func} = year or "
            f"WHERE {col_name} >= start_date AND {col_name} <= end_date. "
            f"Return matching records."
        ]
        
        keywords = extract_keywords(col_name)
        keywords.extend(["created", "started", "in", "year", "date", "when"])
        
        recipes.append({
            "id": recipe_id,
            "doc_type": "query_recipe",
            "text": ". ".join(text_parts),
            "metadata": {
                "model": model_name,
                "table": table_name,
                "column": col_name,
                "join_hints": [],
                "keywords": sorted(set(keywords)),
                "semantics": "Temporal filtering by year or date range",
                "recipe_type": "temporal",
                # Propagate SQL dialect so downstream components can apply dialect-specific handling
                "dialect": dialect,
            },
        })
    
    # "Updated recently" queries
    if "updated" in col_name.lower():
        recipe_id = f"query_recipe:{col_name}_recently"
        text_parts = [
            f"Recipe: {model_name.lower()} {col_name.replace('_', ' ')} recently. "
            f"Query {table_name} table. "
            f"Filter by {col_name} using time range: WHERE {col_name} >= {date_subtract_n} "
            f"or WHERE {col_name} >= {date_subtract_alt}. "
            f"Order by {col_name} DESC to show most recent first. "
            f"Return recently updated records."
        ]
        
        keywords = extract_keywords(col_name)
        keywords.extend(["updated", "recently", "recent", "modified", "changed", "latest"])
        
        recipes.append({
            "id": recipe_id,
            "doc_type": "query_recipe",
            "text": ". ".join(text_parts),
            "metadata": {
                "model": model_name,
                "table": table_name,
                "column": col_name,
                "join_hints": [],
                "keywords": sorted(set(keywords)),
                "semantics": "Temporal filtering for recent updates",
                "recipe_type": "temporal",
                # Propagate SQL dialect so downstream components can apply dialect-specific handling
                "dialect": dialect,
            },
        })
    
    # "Last week" or "in the last week" queries
    recipe_id = f"query_recipe:{col_name}_last_week"
    text_parts = [
        f"Recipe: {model_name.lower()} {col_name.replace('_', ' ')} in the last week. "
        f"Query {table_name} table. "
        f"Filter by {col_name} >= {date_subtract_7} or "
        f"WHERE {col_name} >= {date_subtract_alt_7}. "
        f"Return records from the last week."
    ]
    
    keywords = extract_keywords(col_name)
    keywords.extend(["last week", "recent", "past", "since"])
    
    recipes.append({
        "id": recipe_id,
        "doc_type": "query_recipe",
        "text": ". ".join(text_parts),
        "metadata": {
            "model": model_name,
            "table": table_name,
            "column": col_name,
            "join_hints": [],
            "keywords": sorted(set(keywords)),
                "semantics": "Temporal filtering for last week",
                "recipe_type": "temporal",
                # Propagate SQL dialect so downstream components can apply dialect-specific handling
                "dialect": dialect,
        },
    })
    
    return recipes


def generate_status_recipes(
    model: Dict[str, Any],
    column: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate recipes for status/enum filtering queries."""
    recipes = []
    col_name = column["name"]
    table_name = model["table"]
    model_name = model["model"]
    
    if "status" not in col_name.lower() and "state" not in col_name.lower():
        return recipes
    
    # Status filtering queries
    status_keywords = ["running", "completed", "active", "failed", "pending", "success"]
    
    for status in status_keywords:
        recipe_id = f"query_recipe:{col_name}_{status}"
        text_parts = [
            f"Recipe: {model_name.lower()} with status {status}. "
            f"Query {table_name} table. "
            f"Filter by {col_name} = '{status}' (or appropriate status value). "
            f"Use COUNT(*) to count how many {model_name.lower()}s are {status}. "
            f"Return matching records or count."
        ]
        
        keywords = extract_keywords(col_name)
        keywords.extend([status, "status", "state", "condition"])
        
        recipes.append({
            "id": recipe_id,
            "doc_type": "query_recipe",
            "text": ". ".join(text_parts),
            "metadata": {
                "model": model_name,
                "table": table_name,
                "column": col_name,
                "join_hints": [],
                "keywords": sorted(set(keywords)),
                "semantics": f"Status filtering: {status}",
                "recipe_type": "status",
            },
        })
    
    # "How many are running" type queries
    recipe_id = f"query_recipe:how_many_{col_name}"
    text_parts = [
        f"Recipe: how many {model_name.lower()}s with specific status. "
        f"Query {table_name} table. "
        f"Use COUNT(*) with filter WHERE {col_name} = 'status_value'. "
        f"Return the count of records matching the status condition."
    ]
    
    keywords = extract_keywords(col_name)
    keywords.extend(["how many", "count", "number", "status", "state"])
    
    recipes.append({
        "id": recipe_id,
        "doc_type": "query_recipe",
        "text": ". ".join(text_parts),
        "metadata": {
            "model": model_name,
            "table": table_name,
            "column": col_name,
            "join_hints": [],
            "keywords": sorted(set(keywords)),
            "semantics": "Count by status",
            "recipe_type": "status",
        },
    })
    
    return recipes


def generate_generic_recipes(
    model: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate recipes for generic query patterns."""
    recipes = []
    table_name = model["table"]
    model_name = model["model"]
    model_name_lower = model_name.lower()
    
    # Find name and description columns
    name_col = next((c for c in model["columns"] if "name" in c["name"].lower()), None)
    desc_col = next((c for c in model["columns"] if "description" in c["name"].lower()), None)
    
    # "List all names" recipe
    if name_col:
        recipe_id = f"query_recipe:list_all_{table_name}_names"
        text_parts = [
            f"Recipe: list all {model_name_lower} names. "
            f"Query {table_name} table. "
            f"Use SELECT {name_col['name']} FROM {table_name}. "
            f"Optionally filter by conditions if specified. "
            f"Order by {name_col['name']} ASC for alphabetical order. "
            f"Return all {name_col['name']} values."
        ]
        
        keywords = extract_keywords(name_col["name"])
        keywords.extend(["list", "all", "names", "list all"])
        
        recipes.append({
            "id": recipe_id,
            "doc_type": "query_recipe",
            "text": ". ".join(text_parts),
            "metadata": {
                "model": model_name,
                "table": table_name,
                "column": name_col["name"],
                "join_hints": [],
                "keywords": sorted(set(keywords)),
                "semantics": "Simple SELECT query for names",
                "recipe_type": "generic",
            },
        })
    
    # "Names and descriptions" recipe
    if name_col and desc_col:
        recipe_id = f"query_recipe:{table_name}_names_and_descriptions"
        text_parts = [
            f"Recipe: {model_name_lower} names and descriptions. "
            f"Query {table_name} table. "
            f"Use SELECT {name_col['name']}, {desc_col['name']} FROM {table_name}. "
            f"Optionally filter by conditions if specified. "
            f"Return {name_col['name']} and {desc_col['name']} columns."
        ]
        
        keywords = extract_keywords(f"{name_col['name']} {desc_col['name']}")
        keywords.extend(["names", "descriptions", "and"])
        
        recipes.append({
            "id": recipe_id,
            "doc_type": "query_recipe",
            "text": ". ".join(text_parts),
            "metadata": {
                "model": model_name,
                "table": table_name,
                "column": None,
                "join_hints": [],
                "keywords": sorted(set(keywords)),
                "semantics": "SELECT multiple columns",
                "recipe_type": "generic",
            },
        })
    
    # "All [model]s" recipe
    recipe_id = f"query_recipe:all_{table_name}"
    text_parts = [
        f"Recipe: all {model_name_lower}s. "
        f"Query {table_name} table. "
        f"Use SELECT * FROM {table_name} or SELECT specific columns. "
        f"Optionally filter by conditions if specified. "
        f"Return all records from {table_name}."
    ]
    
    keywords = extract_keywords(model_name)
    keywords.extend(["all", "list", "every"])
    
    recipes.append({
        "id": recipe_id,
        "doc_type": "query_recipe",
        "text": ". ".join(text_parts),
        "metadata": {
            "model": model_name,
            "table": table_name,
            "column": None,
            "join_hints": [],
            "keywords": sorted(set(keywords)),
            "semantics": "Simple SELECT all query",
            "recipe_type": "generic",
        },
    })
    
    return recipes


def generate_documents(schema_data: Dict[str, Any], dialect: str = "postgresql") -> List[Dict[str, Any]]:
    """Generate all RAG documents from schema data.
    
    Args:
        schema_data: Schema data dictionary
        dialect: Database dialect (postgresql, mysql, mssql, sqlite)
    """
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
            
            # 4. Generate aggregation recipes for numeric/count columns
            agg_recipes = generate_aggregation_recipes(model, column)
            documents.extend(agg_recipes)
            
            # 5. Generate temporal recipes for datetime columns
            temp_recipes = generate_temporal_recipes(model, column, dialect=dialect)
            documents.extend(temp_recipes)
            
            # 6. Generate status recipes for status/state columns
            status_recipes = generate_status_recipes(model, column)
            documents.extend(status_recipes)
        
        # 7. Generate relationship recipes for models with relationships
        rel_recipes = generate_relationship_recipes(model, models)
        documents.extend(rel_recipes)
        
        # 8. Generate generic recipes for common patterns
        generic_recipes = generate_generic_recipes(model)
        documents.extend(generic_recipes)
    
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
    parser.add_argument(
        "--dialect",
        type=str,
        default="postgresql",
        choices=["postgresql", "mysql", "mssql", "sqlite"],
        help="Database dialect for SQL syntax in query recipes (default: postgresql)",
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
    
    print(f"Generating documents with dialect: {args.dialect}...")
    documents = generate_documents(schema_data, dialect=args.dialect)
    
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
