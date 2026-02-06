class Dialect:
    def allowed_statements(self):
        return []

    def max_subquery_depth(self):
        return 1

    def forbidden_keywords(self):
        return []

    def validate_statement(self, stmt, tokens):
        return []

    def validate_clauses(self, stmt, tokens):
        return []

    def validate_ddl(self, stmt, tokens):
        return []
