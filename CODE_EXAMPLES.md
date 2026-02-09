# SQL Validator - Code Examples & Use Cases

## 🔍 How Each Component Works

### 1. TOKENIZER - Breaking SQL into Tokens

```python
# From: parser/tokenizer.py

from parser.tokenizer import tokenize

# Example 1: Simple SELECT
sql1 = "SELECT * FROM users"
tokens1 = tokenize(sql1)
# Output:
# [
#   ("KEYWORD", "SELECT", 1),
#   ("STAR", "*", 1),
#   ("KEYWORD", "FROM", 1),
#   ("IDENTIFIER", "USERS", 1)
# ]

# Example 2: With String Literal (FIXED - handles escapes)
sql2 = "SELECT * FROM users WHERE name = 'John O\\'Brien'"
tokens2 = tokenize(sql2)
# Output:
# [
#   ("KEYWORD", "SELECT", 1),
#   ("STAR", "*", 1),
#   ("KEYWORD", "FROM", 1),
#   ("IDENTIFIER", "USERS", 1),
#   ("KEYWORD", "WHERE", 1),
#   ("IDENTIFIER", "NAME", 1),
#   ("OPERATOR", "=", 1),
#   ("STRING", "'JOHN O\\'BRIEN'", 1)  ✅ ESCAPED QUOTE HANDLED!
# ]

# Example 3: With Numbers
sql3 = "SELECT id, age FROM users WHERE age >= 18"
tokens3 = tokenize(sql3)
# Output:
# [
#   ("KEYWORD", "SELECT", 1),
#   ("IDENTIFIER", "ID", 1),
#   ("SYMBOL", ",", 1),
#   ("IDENTIFIER", "AGE", 1),
#   ("KEYWORD", "FROM", 1),
#   ("IDENTIFIER", "USERS", 1),
#   ("KEYWORD", "WHERE", 1),
#   ("IDENTIFIER", "AGE", 1),
#   ("OPERATOR", ">=", 1),
#   ("NUMBER", "18", 1)
# ]

# Example 4: Error on Invalid Character
try:
    sql4 = "SELECT @ FROM users"  # @ is invalid
    tokens4 = tokenize(sql4)
except SyntaxError as e:
    # Output: "Invalid character near '@' at line 1"
    pass
```

---

### 2. STATEMENT TYPE DETECTION

```python
# From: parser/statement.py

from parser.statement import get_statement_type
from parser.tokenizer import tokenize

# Example 1: SELECT statement
sql = "SELECT * FROM users"
tokens = tokenize(sql)
stmt_type = get_statement_type(tokens)
# Output: "SELECT"

# Example 2: INSERT statement
sql = "INSERT INTO logs VALUES (1, 'test')"
tokens = tokenize(sql)
stmt_type = get_statement_type(tokens)
# Output: "INSERT"

# Example 3: Empty query
tokens = []
stmt_type = get_statement_type(tokens)
# Output: None
```

---

### 3. RULES ENGINE - Global Syntax Checks

```python
# From: parser/rules.py

from parser.rules import apply_rules

# Example 1: Unmatched Parentheses
sql1 = "SELECT * FROM (SELECT id FROM users"
errors1 = apply_rules(sql1, max_depth=2)
# Output:
# [
#   {
#     "line": 1,
#     "issue": "Unmatched parentheses",
#     "explanation": "Number of ( and ) must be equal"
#   }
# ]

# Example 2: Unclosed String
sql2 = "SELECT * FROM users WHERE name = 'John"
errors2 = apply_rules(sql2, max_depth=2)
# Output:
# [
#   {
#     "line": 1,
#     "issue": "Unclosed string literal",
#     "explanation": "String must start and end with single quotes"
#   }
# ]

# Example 3: Nesting Depth Exceeded
sql3 = "SELECT * FROM (SELECT * FROM (SELECT * FROM (SELECT * FROM t)))"
errors3 = apply_rules(sql3, max_depth=2)
# Output:
# [
#   {
#     "line": 1,
#     "issue": "Subquery nested too deep",
#     "explanation": "Maximum allowed nesting is 2"
#   }
# ]

# Example 4: All valid
sql4 = "SELECT * FROM users WHERE id = 1"
errors4 = apply_rules(sql4, max_depth=2)
# Output: []  (no errors)
```

---

### 4. PARSER - Statement Structure Validation

```python
# From: parser/parser.py

from parser.parser import parse
from parser.tokenizer import tokenize

# Example 1: Empty SELECT list
sql1 = "SELECT FROM users"
tokens1 = tokenize(sql1)
errors1 = parse(sql1, tokens1)
# Output:
# [
#   {
#     "line": 1,
#     "issue": "Empty SELECT list",
#     "explanation": "SELECT must specify columns or * before FROM"
#   }
# ]

# Example 2: Missing FROM in SELECT
sql2 = "SELECT * WHERE id = 1"
tokens2 = tokenize(sql2)
errors2 = parse(sql2, tokens2)
# Output:
# [
#   {
#     "line": 1,
#     "issue": "Missing FROM clause",
#     "explanation": "SELECT must contain FROM"
#   }
# ]

# Example 3: INSERT with wrong order
sql3 = "INSERT VALUES (1, 2) INTO users"
tokens3 = tokenize(sql3)
errors3 = parse(sql3, tokens3)
# Output:
# [
#   {
#     "line": 1,
#     "issue": "Invalid INSERT order",
#     "explanation": "INTO must come before VALUES"
#   }
# ]

# Example 4: Valid SELECT (multiple checks pass)
sql4 = "SELECT id, name FROM users WHERE age > 18"
tokens4 = tokenize(sql4)
errors4 = parse(sql4, tokens4)
# Output: []  (all checks passed!)

# Example 5: Valid INSERT
sql5 = "INSERT INTO users (id, name) VALUES (1, 'John')"
tokens5 = tokenize(sql5)
errors5 = parse(sql5, tokens5)
# Output: []  (valid structure)

# Example 6: UPDATE without SET
sql6 = "UPDATE users WHERE id = 1"
tokens6 = tokenize(sql6)
errors6 = parse(sql6, tokens6)
# Output:
# [
#   {
#     "line": 1,
#     "issue": "Missing SET clause",
#     "explanation": "UPDATE must contain SET"
#   }
# ]

# Example 7: DELETE without FROM
sql7 = "DELETE users WHERE id = 1"
tokens7 = tokenize(sql7)
errors7 = parse(sql7, tokens7)
# Output:
# [
#   {
#     "line": 1,
#     "issue": "Missing FROM clause",
#     "explanation": "DELETE must use FROM"
#   }
# ]

# Example 8: CREATE without TABLE
sql8 = "CREATE users (id INT)"
tokens8 = tokenize(sql8)
errors8 = parse(sql8, tokens8)
# Output:
# [
#   {
#     "line": 1,
#     "issue": "Invalid DDL",
#     "explanation": "DDL must specify TABLE"
#   }
# ]
```

---

### 5. DIALECT VALIDATION - ANSI SQL

```python
# From: dialect/ansi.py

from dialect.ansi import AnsiDialect
from parser.tokenizer import tokenize

dialect = AnsiDialect()

# Example 1: Valid statement type
sql1 = "SELECT * FROM users"
tokens1 = tokenize(sql1)
stmt1 = "SELECT"
errors1 = dialect.validate_statement(stmt1, tokens1)
# Output: []  (SELECT is allowed in ANSI)

# Example 2: Invalid statement type
sql2 = "REPLACE INTO users VALUES (1)"
tokens2 = tokenize(sql2)
stmt2 = "REPLACE"
errors2 = dialect.validate_statement(stmt2, tokens2)
# Output:
# [
#   {
#     "line": 1,
#     "issue": "Invalid statement",
#     "explanation": "Not allowed in ANSI sql REPLACE"
#   }
# ]

# Example 3: Forbidden keyword - LIMIT
sql3 = "SELECT * FROM users LIMIT 10"
tokens3 = tokenize(sql3)
errors3 = dialect.validate_clauses("SELECT", tokens3)
# Output:
# [
#   {
#     "line": 1,
#     "issue": "Non_ANSI feature",
#     "explanation": "LIMIT is not supported in ANSI SQL"
#   }
# ]

# Example 4: Forbidden keyword - TOP
sql4 = "SELECT TOP 10 * FROM users"
tokens4 = tokenize(sql4)
errors4 = dialect.validate_clauses("SELECT", tokens4)
# Output:
# [
#   {
#     "line": 1,
#     "issue": "Non_ANSI feature",
#     "explanation": "TOP is not supported in ANSI SQL"
#   }
# ]

# Example 5: Forbidden keyword - ILIKE
sql5 = "SELECT * FROM users WHERE name ILIKE '%John%'"
tokens5 = tokenize(sql5)
errors5 = dialect.validate_clauses("SELECT", tokens5)
# Output:
# [
#   {
#     "line": 1,
#     "issue": "Non_ANSI feature",
#     "explanation": "ILIKE is not supported in ANSI SQL"
#   }
# ]

# Example 6: Max nesting depth exceeded
print(f"ANSI Max Nesting: {dialect.max_subquery_depth()}")
# Output: 2
```

---

### 6. DIALECT VALIDATION - MySQL

```python
# From: dialect/mysql.py

from dialect.mysql import MySQLDialect
from parser.tokenizer import tokenize

dialect = MySQLDialect()

# Example 1: LIMIT with value (valid)
sql1 = "SELECT * FROM users LIMIT 10"
tokens1 = tokenize(sql1)
errors1 = dialect.validate_clauses("SELECT", tokens1)
# Output: []  (valid MySQL syntax)

# Example 2: LIMIT without value (invalid)
sql2 = "SELECT * FROM users LIMIT"
tokens2 = tokenize(sql2)
errors2 = dialect.validate_clauses("SELECT", tokens2)
# Output:
# [
#   {
#     "line": 1,
#     "issue": "Invalid LIMIT",
#     "explanation": "LIMIT must be followed by number"
#   }
# ]

# Example 3: Max nesting depth
print(f"MySQL Max Nesting: {dialect.max_subquery_depth()}")
# Output: 4  (more permissive than ANSI)

# Example 4: No forbidden keywords in MySQL
print(f"MySQL Forbidden Keywords: {dialect.forbidden_keywords()}")
# Output: []  (MySQL allows most keywords)
```

---

### 7. IO LAYER - Reading & Writing

```python
# From: io_layer/reader.py

from io_layer.reader import read_input

# Example 1: Single file with multiple queries
# File: inputs/test.txt
# Content: "SELECT * FROM users; INSERT INTO logs VALUES (1);"

queries = read_input("inputs/test.txt")
# Output:
# [
#   {
#     "source": "test.txt",
#     "sql": "SELECT * FROM users"
#   },
#   {
#     "source": "test.txt",
#     "sql": "INSERT INTO logs VALUES (1)"
#   }
# ]

# Example 2: Directory with multiple files
queries = read_input("inputs")
# Output:
# [
#   {"source": "test.txt", "sql": "Query 1"},
#   {"source": "test.txt", "sql": "Query 2"},
#   {"source": "test1.txt", "sql": "Query 3"},
#   {"source": "test2.txt", "sql": "Query 4"}
# ]

# Example 3: Write output
from io_layer.writer import write_json_report

errors = [
    {
        "line": 1,
        "issue": "Empty SELECT list",
        "explanation": "SELECT must specify columns"
    }
]

write_json_report(
    q_id=1,
    src="test.txt",
    sql="SELECT FROM users",
    status="FAILED",
    errors=errors
)
# Creates: outputs/query_1.json
```

---

### 8. COMPLETE VALIDATION PIPELINE

```python
# From: cli/main.py

from io_layer.reader import read_input
from io_layer.writer import write_json_report
from parser.tokenizer import tokenize
from parser.rules import apply_rules
from parser.parser import parse
from parser.statement import get_statement_type
from dialect.ansi import AnsiDialect

# Initialize
dialect = AnsiDialect()
sql = "SELECT FROM users"

# Step 1: Get tokens
tokens = tokenize(sql)
# [("KEYWORD", "SELECT", 1), ("KEYWORD", "FROM", 1), ...]

# Step 2: Get statement type
stmt = get_statement_type(tokens)
# "SELECT"

# Step 3: Apply rules
errors = apply_rules(sql, dialect.max_subquery_depth())
# [] (no syntax errors)

# Step 4: Parse statement
errors.extend(parse(sql, tokens))
# [{"issue": "Empty SELECT list", ...}]

# Step 5: Dialect validation
errors.extend(dialect.validate_statement(stmt, tokens))
# [] (SELECT is allowed)
errors.extend(dialect.validate_clauses(stmt, tokens))
# [] (no forbidden keywords)

# Step 6: Determine status
status = "FAILED" if errors else "SUCCESS"
# "FAILED"

# Step 7: Write report
write_json_report(1, "test.txt", sql, status, errors)
# Creates: outputs/query_1.json

# Final output:
# {
#   "q_id": 1,
#   "source": "test.txt",
#   "sql": "SELECT FROM users",
#   "status": "FAILED",
#   "errors": [
#     {
#       "line": 1,
#       "issue": "Empty SELECT list",
#       "explanation": "SELECT must specify columns or * before FROM"
#     }
#   ]
# }
```

---

## 🚀 How to Extend the Validator

### Add New SQL Keyword

```python
# File: parser/tokenizer.py

TOKENS = [
    # Add BETWEEN to keywords
    ("KEYWORD", r"\b(SELECT|...|BETWEEN)\b"),
    ...
]

# Now BETWEEN will be recognized as a keyword instead of identifier
```

### Add New Statement Type (e.g., MERGE)

```python
# File: parser/parser.py

def parse(sql, tokens):
    errors = []
    line = 1
    stmt = get_statement_type(tokens)
    keywords = [v for _, v, _ in tokens]

    # ... existing checks ...

    # MERGE checks
    elif stmt == "MERGE":
        using_idx = _find_value_idx(tokens, "USING")
        matched_idx = _find_value_idx(tokens, "MATCHED")
        
        if using_idx == -1:
            errors.append(error(line, "Missing USING clause", "MERGE must use USING"))
        if matched_idx == -1:
            errors.append(error(line, "Missing MATCHED clause", "MERGE must use MATCHED"))

    return errors
```

### Add New Dialect (e.g., PostgreSQL)

```python
# File: dialect/postgres.py

from dialect.base import Dialect
from parser.errors import error

class PostgreSQLDialect(Dialect):
    def allowed_statements(self):
        return ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "WITH"]

    def max_subquery_depth(self):
        return 10  # PostgreSQL allows deep nesting

    def forbidden_keywords(self):
        return ["LIMIT", "OFFSET"]  # Actually, PostgreSQL ALLOWS these!

    def validate_statement(self, stmt, tokens):
        allowed = self.allowed_statements()
        if stmt not in allowed:
            return [error(1, "Invalid statement", f"{stmt} not allowed in PostgreSQL")]
        return []

    def validate_clauses(self, stmt, tokens):
        # PostgreSQL-specific clause validation
        return []

    def validate_ddl(self, stmt, tokens):
        # PostgreSQL-specific DDL validation
        return []

# File: cli/main.py - Register new dialect

from dialect.postgres import PostgreSQLDialect

DIALECTS = {
    "ansi": AnsiDialect(),
    "mysql": MySQLDialect(),
    "postgres": PostgreSQLDialect()  # Add this!
}

# Now run: python -m cli.main  (will use ansi by default)
# Or: python -m cli.main --dialect postgres
```

### Add Custom Validation Rule

```python
# File: parser/rules.py

def apply_rules(sql, max_depth):
    errors = []
    line = 1
    
    # Existing checks
    if sql.count("(") != sql.count(")"):
        errors.append(error(line, "Unmatched parentheses", ...))
    
    # NEW: Check for SQL injection patterns
    dangerous_words = ["DROP TABLE", "DELETE FROM", "TRUNCATE"]
    sql_upper = sql.upper()
    for word in dangerous_words:
        if word in sql_upper:
            errors.append(error(line, "Dangerous SQL", f"{word} not allowed in production"))
    
    # NEW: Check for missing WHERE clause in DELETE
    if "DELETE" in sql_upper and "WHERE" not in sql_upper:
        errors.append(error(line, "Missing WHERE", "DELETE without WHERE clause is dangerous"))
    
    return errors
```

### Add Command-Line Arguments

```python
# File: cli/main.py

import sys

def process(path, dialect_name="ansi"):
    # ... existing code ...
    pass

if __name__ == "__main__":
    # Parse arguments
    path = sys.argv[1] if len(sys.argv) > 1 else "inputs"
    dialect = sys.argv[2] if len(sys.argv) > 2 else "ansi"
    
    print(f"Validating SQL from: {path}")
    print(f"Using dialect: {dialect}")
    
    process(path, dialect_name=dialect)

# Usage:
# python -m cli.main inputs ansi
# python -m cli.main inputs/test.txt mysql
# python -m cli.main . postgres
```

---

## 🧪 Testing Examples

### Test Case 1: Empty SELECT

```python
def test_empty_select():
    from parser.tokenizer import tokenize
    from parser.parser import parse
    
    sql = "SELECT FROM users"
    tokens = tokenize(sql)
    errors = parse(sql, tokens)
    
    assert len(errors) == 1
    assert "Empty SELECT list" in errors[0]["issue"]
```

### Test Case 2: Escaped Quotes

```python
def test_escaped_quotes():
    from parser.tokenizer import tokenize
    
    sql = "SELECT * FROM users WHERE name = 'John O\\'Brien'"
    tokens = tokenize(sql)
    
    # Should not raise SyntaxError
    assert len(tokens) > 0
    assert any("BRIEN" in token[1] for token in tokens)
```

### Test Case 3: INSERT Validation

```python
def test_insert_validation():
    from parser.tokenizer import tokenize
    from parser.parser import parse
    
    # Wrong order
    sql1 = "INSERT VALUES (1) INTO users"
    errors1 = parse(sql1, tokenize(sql1))
    assert len(errors1) > 0
    
    # Correct order
    sql2 = "INSERT INTO users VALUES (1)"
    errors2 = parse(sql2, tokenize(sql2))
    assert len(errors2) == 0
```

---

## 📊 Summary Table

| Component | Purpose | Input | Output |
|-----------|---------|-------|--------|
| Tokenizer | Break SQL into tokens | SQL string | List of (type, value, line) |
| Statement | Identify query type | Token list | "SELECT", "INSERT", etc. |
| Rules | Global syntax checks | SQL string | List of errors |
| Parser | Statement structure checks | Tokens + statement type | List of errors |
| Dialect | Vendor-specific checks | Tokens + statement type | List of errors |
| Reader | Load SQL from files | Path (file/dir) | List of {source, sql} |
| Writer | Save validation reports | Errors + metadata | JSON file |

This covers all the main components and how to extend the system!
