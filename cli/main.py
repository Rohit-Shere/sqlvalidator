from io_layer.reader import read_input
from io_layer.writer import write_json_report
from parser.tokenizer import tokenize
from parser.rules import apply_rules
from parser.parser import parse
from dialects.ansi import AnsiDialect
from dialects.mysql import MySQLDialect

DIALECTS = {
    "ansi": AnsiDialect(),
    "mysql": MySQLDialect()
}

def process(path, dialect_name="ansi"):
    dialect = DIALECTS[dialect_name]
    queries = read_input(path)

    for i, q in enumerate(queries, start=1):
        sql = q["sql"]
        src = q["source"]
        errors = []

        try:
            tokens = tokenize(sql)
            stmt = tokens[0][1]
            errors.extend(apply_rules(sql, dialect.max_subquery_depth()))
            errors.extend(parse(sql, tokens))
            errors.extend(dialect.validate_statement(stmt, tokens))
            errors.extend(dialect.validate_clauses(stmt, tokens))
            errors.extend(dialect.validate_ddl(stmt, tokens))
        except Exception as e:
            errors.append({"line": 1, "issue": "Fatal error", "explanation": str(e)})

        status = "FAILED" if errors else "SUCCESS"
        write_json_report(i, src, sql, status, errors)

if __name__ == "__main__":
    process("inputs", dialect_name="ansi")
