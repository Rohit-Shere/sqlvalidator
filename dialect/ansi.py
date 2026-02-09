from dialect.base import Dialect
from parser.errors import error

class AnsiDialect(Dialect):
    def allowed_statements(self):
        return ["SELECT","INSERT","UPDATE","DELETE", "CREATE", "DROP", "ALTER"]

    def max_subquery_depth(self):
        return 2

    def forbidden_keywords(self):
        return["LIMIT","TOP","ILIKE"]

    def validate_statement(self, stmt, tokens):
        if stmt not in self.allowed_statements():
            return [error(1, "Invalid statement", f"Not allowed in ANSI sql {stmt}")]
        return []

    def validate_clauses(self, stmt, tokens):
        errors = []
        # Extract values from 3-tuples (type, value, line)
        keywords = [v for _, v, _ in tokens]
        for k in self.forbidden_keywords():
            if k in keywords:
                errors.append(error(1, "Non_ANSI feature", f"{k} is not supported in ANSI SQL"))
        return errors

    def validate_ddl(self, stmt, tokens):
        return []
