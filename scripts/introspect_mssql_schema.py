#!/usr/bin/env python3
"""Introspect MSSQL Server database schema and export to JSON format.

This script connects to a MSSQL Server database and exports the schema
in the format expected by generate_schema_rag_docs.py.

SECURITY NOTE: This script supports secure password handling. Avoid passing
passwords via command-line arguments as they may be visible in process listings.

Recommended Usage (secure):
    # Option 1: Environment variable (recommended)
    export MSSQL_PASSWORD="your_password"
    python scripts/introspect_mssql_schema.py \
        --server localhost \
        --database mydb \
        --username sa \
        --output artifacts/mssql_models.json

    # Option 2: Interactive prompt (secure)
    python scripts/introspect_mssql_schema.py \
        --server localhost \
        --database mydb \
        --username sa \
        --output artifacts/mssql_models.json
    # You will be prompted securely for the password

    # Option 3: Password file
    python scripts/introspect_mssql_schema.py \
        --server localhost \
        --database mydb \
        --username sa \
        --password-file /path/to/secure/password.txt \
        --output artifacts/mssql_models.json

Alternative (connection string via environment variable):
    export MSSQL_CONNECTION_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=mydb;UID=sa;PWD=your_password"
    python scripts/introspect_mssql_schema.py \
        --output artifacts/mssql_models.json
"""

import argparse
import getpass
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Try to import MSSQL drivers (checked later during connection)
pyodbc = None
pymssql = None
try:
    import pyodbc
except ImportError:
    try:
        import pymssql
    except ImportError:
        pass  # Will check and error during connection attempt


def get_connection(server: str = None, database: str = None, username: str = None,
                  password: str = None, connection_string: str = None):
    """Create database connection."""
    if connection_string:
        if pyodbc:
            return pyodbc.connect(connection_string)
        else:
            # pymssql doesn't support connection strings directly
            # Parse connection string for pymssql
            params = {}
            for part in connection_string.split(';'):
                if '=' in part:
                    key, value = part.split('=', 1)
                    key = key.strip().upper()
                    value = value.strip()
                    # pymssql does not use ODBC driver specification; ignore it if present
                    if key == 'DRIVER':
                        continue
                    if key == 'SERVER':
                        params['server'] = value
                    elif key == 'DATABASE':
                        params['database'] = value
                    elif key in ('UID', 'USER', 'USERNAME'):
                        params['user'] = value
                    elif key in ('PWD', 'PASSWORD'):
                        params['password'] = value
            if not params:
                # Connection string did not contain any parameters usable by pymssql.
                # Fall back to explicit arguments if they were provided.
                if server or database or username or password:
                    return pymssql.connect(server=server, database=database,
                                           user=username, password=password)
                raise ValueError(
                    "Could not parse connection string for pymssql: no SERVER, "
                    "DATABASE, UID/USER, or PWD/PASSWORD parameters found. "
                    "Use --server, --database, --username, --password instead."
                )
            return pymssql.connect(**params)
    else:
        if pyodbc:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password}"
            )
            return pyodbc.connect(conn_str)
        else:
            return pymssql.connect(server=server, database=database,
                                  user=username, password=password)


def get_tables(conn) -> List[str]:
    """Get list of user tables."""
    cursor = conn.cursor()
    query = """
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        AND TABLE_SCHEMA NOT IN ('sys', 'information_schema')
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """
    cursor.execute(query)
    return [(row[0], row[1]) for row in cursor.fetchall()]


def get_columns(conn, schema: str, table: str) -> List[Dict[str, Any]]:
    """Get columns for a table."""
    cursor = conn.cursor()
    query = """
        SELECT 
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.IS_NULLABLE,
            c.COLUMN_DEFAULT,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.NUMERIC_PRECISION,
            c.NUMERIC_SCALE,
            c.DATETIME_PRECISION
        FROM INFORMATION_SCHEMA.COLUMNS c
        WHERE c.TABLE_SCHEMA = ? AND c.TABLE_NAME = ?
        ORDER BY c.ORDINAL_POSITION
    """
    cursor.execute(query, schema, table)
    
    columns = []
    for row in cursor.fetchall():
        col_name, data_type, is_nullable, default, char_max_len, num_precision, num_scale, dt_precision = row
        
        # Map MSSQL types to generic types
        type_mapping = {
            'int': 'Integer',
            'bigint': 'BigInteger',
            'smallint': 'SmallInteger',
            'tinyint': 'SmallInteger',
            'bit': 'Boolean',
            'decimal': 'Numeric',
            'numeric': 'Numeric',
            'float': 'Float',
            'real': 'Float',
            'money': 'Numeric',
            'smallmoney': 'Numeric',
            'char': 'String',
            'varchar': 'String',
            'text': 'Text',
            'nchar': 'String',
            'nvarchar': 'String',
            'ntext': 'Text',
            'date': 'Date',
            'time': 'Time',
            'datetime': 'DateTime',
            'datetime2': 'DateTime',
            'smalldatetime': 'DateTime',
            'datetimeoffset': 'DateTime',
            'timestamp': 'DateTime',
            'uniqueidentifier': 'String',
            'xml': 'Text',
            'json': 'JSON',
            'binary': 'LargeBinary',
            'varbinary': 'LargeBinary',
            'image': 'LargeBinary',
        }
        
        sql_type = type_mapping.get(data_type.lower(), data_type)
        
        # Build full type string
        if sql_type in ['String', 'Numeric']:
            if char_max_len and char_max_len > 0:
                sql_type = f"{sql_type}({char_max_len})"
            elif num_precision and num_scale is not None:
                sql_type = f"{sql_type}({num_precision},{num_scale})"
            elif num_precision:
                sql_type = f"{sql_type}({num_precision})"
        
        column = {
            "name": col_name,
            "type": sql_type,
            "nullable": is_nullable == "YES",
        }
        
        if default:
            column["default"] = default.strip()
        
        columns.append(column)
    
    return columns


def get_foreign_keys(conn, schema: str, table: str) -> Dict[str, List[Dict[str, Any]]]:
    """Get foreign keys for a table."""
    cursor = conn.cursor()
    query = """
        SELECT 
            kcu.COLUMN_NAME,
            ccu.TABLE_SCHEMA AS FOREIGN_TABLE_SCHEMA,
            ccu.TABLE_NAME AS FOREIGN_TABLE_NAME,
            ccu.COLUMN_NAME AS FOREIGN_COLUMN_NAME
        FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            ON rc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
            AND rc.CONSTRAINT_SCHEMA = kcu.CONSTRAINT_SCHEMA
        JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu
            ON rc.UNIQUE_CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
            AND rc.UNIQUE_CONSTRAINT_SCHEMA = ccu.CONSTRAINT_SCHEMA
        WHERE kcu.TABLE_SCHEMA = ? AND kcu.TABLE_NAME = ?
    """
    cursor.execute(query, schema, table)
    
    fk_map = {}
    for row in cursor.fetchall():
        col_name, fk_schema, fk_table, fk_col = row
        if col_name not in fk_map:
            fk_map[col_name] = []
        fk_map[col_name].append({
            "target_table": fk_table,
            "target_column": fk_col,
        })
    
    return fk_map


def get_primary_keys(conn, schema: str, table: str) -> List[str]:
    """Get primary key columns for a table."""
    cursor = conn.cursor()
    query = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        AND CONSTRAINT_NAME IN (
            SELECT CONSTRAINT_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            AND CONSTRAINT_TYPE = 'PRIMARY KEY'
        )
        ORDER BY ORDINAL_POSITION
    """
    cursor.execute(query, schema, table, schema, table)
    return [row[0] for row in cursor.fetchall()]


def get_relationships(conn, schema: str, table: str) -> List[Dict[str, Any]]:
    """Get relationships (foreign keys pointing to this table)."""
    cursor = conn.cursor()
    query = """
        SELECT 
            kcu.TABLE_SCHEMA AS REFERENCING_SCHEMA,
            kcu.TABLE_NAME AS REFERENCING_TABLE,
            kcu.COLUMN_NAME AS REFERENCING_COLUMN,
            ccu.COLUMN_NAME AS REFERENCED_COLUMN
        FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            ON rc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
            AND rc.CONSTRAINT_SCHEMA = kcu.CONSTRAINT_SCHEMA
        JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu
            ON rc.UNIQUE_CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
            AND rc.UNIQUE_CONSTRAINT_SCHEMA = ccu.CONSTRAINT_SCHEMA
        WHERE ccu.TABLE_SCHEMA = ? AND ccu.TABLE_NAME = ?
    """
    cursor.execute(query, schema, table)
    
    relationships = []
    for row in cursor.fetchall():
        ref_schema, ref_table, ref_col, refd_col = row
        relationships.append({
            "name": f"{ref_table}_{ref_col}",
            "target_table": ref_table,
            "target_model": ref_table.replace('_', '').title(),
            "join_pairs": [{
                "local_column": refd_col,
                "remote_table": ref_table,
                "remote_column": ref_col,
            }],
        })
    
    return relationships


def introspect_schema(conn) -> Dict[str, Any]:
    """Introspect entire database schema."""
    models = []
    tables = get_tables(conn)
    
    for schema, table in tables:
        print(f"Processing {schema}.{table}...")
        
        columns = get_columns(conn, schema, table)
        foreign_keys = get_foreign_keys(conn, schema, table)
        relationships = get_relationships(conn, schema, table)
        
        # Add foreign key info to columns
        for col in columns:
            if col["name"] in foreign_keys:
                col["foreign_keys"] = foreign_keys[col["name"]]
        
        # Generate model name from table name
        model_name = ''.join(word.capitalize() for word in table.split('_'))
        
        model = {
            "model": model_name,
            "module": "models",  # Default module name
            "table": table,
            "schema": schema,
            "columns": columns,
            "relationships": relationships,
            "source_file": f"mssql://{schema}.{table}",
        }
        
        models.append(model)
    
    return {"models": models}


def get_password_secure(args) -> str:
    """Get password securely from various sources.
    
    Priority order:
    1. Password file (--password-file)
    2. Environment variable (MSSQL_PASSWORD)
    3. Interactive prompt (getpass)
    
    Returns:
        Password string
        
    Raises:
        SystemExit if password cannot be obtained
    """
    # Option 1: Password file
    if args.password_file:
        password_path = Path(args.password_file)
        if not password_path.exists():
            print(f"Error: Password file not found: {args.password_file}", file=sys.stderr)
            sys.exit(1)
        try:
            with open(password_path, "r", encoding="utf-8") as f:
                password = f.read().strip()
            if not password:
                print(f"Error: Password file is empty: {args.password_file}", file=sys.stderr)
                sys.exit(1)
            return password
        except PermissionError:
            print(f"Error: Cannot read password file (permission denied): {args.password_file}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: Failed to read password file: {type(e).__name__}", file=sys.stderr)
            sys.exit(1)
    
    # Option 2: Environment variable
    password = os.environ.get("MSSQL_PASSWORD")
    if password:
        return password
    
    # Option 3: Interactive prompt
    if sys.stdin.isatty():
        try:
            password = getpass.getpass("Enter MSSQL password: ")
            if not password:
                print("Error: Password cannot be empty", file=sys.stderr)
                sys.exit(1)
            return password
        except (EOFError, KeyboardInterrupt):
            print("\nPassword input cancelled", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: No password provided. Use one of:", file=sys.stderr)
        print("  - Set MSSQL_PASSWORD environment variable", file=sys.stderr)
        print("  - Use --password-file option", file=sys.stderr)
        print("  - Run interactively for secure prompt", file=sys.stderr)
        sys.exit(1)


def get_connection_string_secure() -> str:
    """Get connection string from environment variable.
    
    Returns:
        Connection string or None if not set
    """
    return os.environ.get("MSSQL_CONNECTION_STRING")


def main():
    parser = argparse.ArgumentParser(
        description="Introspect MSSQL Server schema and export to JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Security Notes:
  - Passwords are obtained securely via environment variable, file, or interactive prompt
  - Avoid passing passwords on command line as they may be visible in process listings
  - Set MSSQL_PASSWORD environment variable or use --password-file for automation
  - Connection strings can be set via MSSQL_CONNECTION_STRING environment variable
        """
    )
    
    # Connection options
    parser.add_argument(
        "--connection-string",
        type=str,
        help="ODBC connection string. For security, prefer setting MSSQL_CONNECTION_STRING env var instead.",
    )
    parser.add_argument(
        "--server",
        type=str,
        help="Database server hostname or IP",
    )
    parser.add_argument(
        "--database",
        type=str,
        help="Database name",
    )
    parser.add_argument(
        "--username",
        type=str,
        help="Database username",
    )
    parser.add_argument(
        "--password-file",
        type=str,
        help="Path to file containing password (more secure than command-line)",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output JSON file path",
    )
    
    args = parser.parse_args()
    
    # Determine connection method
    connection_string = args.connection_string or get_connection_string_secure()
    
    if connection_string:
        # Using connection string
        if not pyodbc:
            try:
                import pymssql
            except ImportError:
                print("Error: MSSQL driver required. Install with: pip install pyodbc or pip install pymssql", file=sys.stderr)
                sys.exit(1)
    elif args.server:
        # Using individual parameters - need database and username
        if not args.database:
            parser.error("--database is required when using --server")
        if not args.username:
            parser.error("--username is required when using --server")
    else:
        parser.error("Either --server or --connection-string (or MSSQL_CONNECTION_STRING env var) is required")
    
    # Check for MSSQL driver availability
    if not pyodbc and not pymssql:
        print("Error: Missing MSSQL driver. Install one of:", file=sys.stderr)
        print("  pip install pyodbc", file=sys.stderr)
        print("  pip install pymssql", file=sys.stderr)
        return 1
    
    # Get password securely if using individual parameters
    password = None
    if not connection_string:
        password = get_password_secure(args)
    
    # Connect to database
    print("Connecting to database...")
    conn = None
    try:
        if connection_string:
            conn = get_connection(connection_string=connection_string)
        else:
            conn = get_connection(
                server=args.server,
                database=args.database,
                username=args.username,
                password=password,
            )
        print("Connected successfully!")
    except Exception as e:
        # Sanitize error message to avoid leaking credentials
        error_type = type(e).__name__
        error_msg = str(e)
        
        # Remove potential password from error message
        if password and password in error_msg:
            error_msg = error_msg.replace(password, "***")
        if connection_string:
            # Mask any PWD= values in connection string errors
            import re
            error_msg = re.sub(r'PWD=[^;]*', 'PWD=***', error_msg, flags=re.IGNORECASE)
            error_msg = re.sub(r'PASSWORD=[^;]*', 'PASSWORD=***', error_msg, flags=re.IGNORECASE)
        
        print(f"Error connecting to database: {error_type}", file=sys.stderr)
        print(f"Details: {error_msg}", file=sys.stderr)
        print("\nPlease verify:", file=sys.stderr)
        print("  - Server hostname/IP is correct and reachable", file=sys.stderr)
        print("  - Database name exists", file=sys.stderr)
        print("  - Username and password are correct", file=sys.stderr)
        print("  - Required ODBC driver is installed", file=sys.stderr)
        if conn:
            conn.close()
        return 1
    
    try:
        # Introspect schema
        print("Introspecting schema...")
        schema_data = introspect_schema(conn)
        
        # Write output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Writing schema to {output_path}...")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(schema_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Exported {len(schema_data['models'])} models to {output_path}")
        
    except Exception as e:
        # Sanitize error - don't print full traceback which may contain credentials
        error_type = type(e).__name__
        error_msg = str(e)
        
        # Mask potential credentials in error messages
        if password and password in error_msg:
            error_msg = error_msg.replace(password, "***")
        
        print(f"Error introspecting schema: {error_type}", file=sys.stderr)
        print(f"Details: {error_msg}", file=sys.stderr)
        return 1
    finally:
        conn.close()
    
    return 0


if __name__ == "__main__":
    exit(main())
