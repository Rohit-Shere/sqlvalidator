from io_layer.reader import read_input
from io_layer.writer import write_json_report
from parser.tokenizer import tokenize
from parser.rules import apply_rules
from parser.parser import parse
from parser.statement import get_statement_type
from dialect.ansi import AnsiDialect
from dialect.mysql import MySQLDialect
import argparse
import sys
import os

DIALECTS = {
    "ansi": AnsiDialect(),
    "mysql": MySQLDialect()
}

def process(path, dialect_name="ansi"):
    """
    Process SQL queries from input files and generate validation reports.
    
    Args:
        path: File or directory path containing SQL queries
        dialect_name: SQL dialect to validate against (ansi, mysql)
    """
    dialect = DIALECTS.get(dialect_name)
    if not dialect:
        raise ValueError(f"Unknown dialect: {dialect_name}. Available: {list(DIALECTS.keys())}")
    
    queries = read_input(path)
    
    if not queries:
        print(f"⚠️  No queries found in {path}")
        return
    
    stats = {"total": 0, "passed": 0, "failed": 0}
    
    for i, q in enumerate(queries, start=1):
        sql = q["sql"]
        src = q["source"]
        errors = []
        stats["total"] += 1

        try:
            tokens = tokenize(sql)
            stmt = get_statement_type(tokens)
            
            # Apply all validation layers
            errors.extend(apply_rules(sql, dialect.max_subquery_depth()))
            errors.extend(parse(sql, tokens))
            
            if stmt:
                errors.extend(dialect.validate_statement(stmt, tokens))
                errors.extend(dialect.validate_clauses(stmt, tokens))
                errors.extend(dialect.validate_ddl(stmt, tokens))
                
        except SyntaxError as e:
            errors.append({"line": 1, "issue": "Syntax Error", "explanation": str(e)})
        except Exception as e:
            errors.append({"line": 1, "issue": "Fatal error", "explanation": str(e)})

        status = "FAILED" if errors else "SUCCESS"
        if status == "SUCCESS":
            stats["passed"] += 1
        else:
            stats["failed"] += 1
            
        write_json_report(i, src, sql, status, errors)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Validation Summary")
    print(f"{'='*60}")
    print(f"Total Queries: {stats['total']}")
    print(f"✅ Passed: {stats['passed']}")
    print(f"❌ Failed: {stats['failed']}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="SQL Query Validator - Validates SQL queries against specified dialect",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m cli.main inputs --dialect ansi
  python -m cli.main inputs/query.txt --dialect mysql
  python -m cli.main ~/sql_files --dialect ansi
        """
    )
    
    # Required argument: path to SQL file or directory
    parser.add_argument(
        "path",
        metavar="PATH",
        help="Path to SQL file or directory containing SQL files (required)"
    )
    
    # Optional argument: dialect
    parser.add_argument(
        "--dialect",
        "-d",
        choices=list(DIALECTS.keys()),
        default="ansi",
        help="SQL dialect to validate against (default: ansi)"
    )
    
    # Parse command-line arguments
    args = parser.parse_args()
    
    # Validate that the path exists
    if not os.path.exists(args.path):
        print(f"❌ Error: Path does not exist: {args.path}")
        sys.exit(1)
    
    # Process the SQL queries
    try:
        process(args.path, dialect_name=args.dialect)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
