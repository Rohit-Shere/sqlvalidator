# SQL Validator - Technical Overview \& Architecture Guide

## 📋 Project Summary

**SQL Validator** is a multi-dialect SQL query validation engine that:

* Reads SQL queries from files
* Tokenizes and parses them
* Validates against ANSI SQL and MySQL rules
* Generates JSON reports with detailed error messages

Think of it like a **linter for SQL** - similar to ESLint for JavaScript.

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER INPUT (CLI)                          │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                    IO LAYER (reader.py)                          │
│        Reads SQL files from inputs/ directory or single file     │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                  TOKENIZER (tokenizer.py)                        │
│    Breaks SQL string into tokens: KEYWORD, IDENTIFIER, etc.      │
└──────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┬─────────────────────┐
        ↓                     ↓                     ↓
 ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐
 │ RULES ENGINE   │  │  PARSER          │  │  DIALECT LAYER  │
 │ (rules.py)     │  │  (parser.py)     │  │  (ansi/mysql)   │
 └────────────────┘  └──────────────────┘  └─────────────────┘
        ↓                     ↓                     ↓
  Syntax Rules       Statement Structure   Dialect-Specific Rules
        ↓                     ↓                     ↓
        └─────────────────────┴─────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                    OUTPUT LAYER (writer.py)                      │
│           Writes validation results as JSON reports              │
└──────────────────────────────────────────────────────────────────┘
                              ↓
                         outputs/\*.json
```

---

## 📂 File Structure \& Responsibilities

### **1. IO Layer** - Input/Output Operations

#### `io\_layer/reader.py` - Read SQL Queries

```python
# FIXED: Now uses semicolon (;) splitting instead of line-based splitting
# This correctly handles multi-query files
```

**What it does:**

* Reads SQL queries from files
* Handles both single files and directories
* Splits multiple queries using semicolon delimiter
* Returns list of dictionaries: `{"source": filename, "sql": query}`

**Example Input (`inputs/test.txt`):**

```sql
SELECT \* FROM users;
INSERT INTO logs VALUES (1, 'test');
```

**Output:**

```python
\[
    {"source": "test.txt", "sql": "SELECT \* FROM users"},
    {"source": "test.txt", "sql": "INSERT INTO logs VALUES (1, 'test')"}
]
```

#### `io\_layer/writer.py` - Write JSON Reports

```python
# Writes one JSON file per query
# Format: outputs/query\_{id}.json
```

**Example Output (`outputs/query\_1.json`):**

```json
{
    "q\_id": 1,
    "source": "test.txt",
    "sql": "SELECT \* FROM users",
    "status": "SUCCESS",
    "errors": \[]
}
```

---

### **2. Parser Layer** - Tokenization \& Parsing

#### `parser/tokenizer.py` - Break SQL into Tokens

```
Input SQL:  "SELECT \* FROM users WHERE id = 1"
                           ↓
Output:     \[
              ("KEYWORD", "SELECT", 1),
              ("STAR", "\*", 1),
              ("KEYWORD", "FROM", 1),
              ("IDENTIFIER", "USERS", 1),
              ("KEYWORD", "WHERE", 1),
              ("IDENTIFIER", "ID", 1),
              ("OPERATOR", "=", 1),
              ("NUMBER", "1", 1)
            ]
```

**Token Types:**

|Type|Pattern|Example|
|-|-|-|
|KEYWORD|`\\b(SELECT\|FROM\|WHERE...)`|SELECT, INSERT, UPDATE|
|IDENTIFIER|`\[a-zA-Z\_]\[a-zA-Z0-9\_]\*`|users, employee\_id|
|NUMBER|`\\d+`|123, 456|
|STRING|`'(?:\[^'\\\\]\|\\\\.)\*'`|'John O'Brien'|
|OPERATOR|`(=\|<\|>\|!=...)`|=, >=, !=|
|SYMBOL|`\[(),;]`|(, ), ;|
|STAR|`\\\*`|\*|

**Key Improvements Made:**
✅ Fixed: Escaped quotes with regex `'(?:\[^'\\\\]|\\\\.)\*'`

* Now handles: `'John O\\'Brien'`, `'can\\'t'` correctly
  ✅ Added: Line number tracking for better error messages
* Each token includes its line number: `(type, value, line)`

---

#### `parser/statement.py` - Identify Statement Type

```python
def get\_statement\_type(tokens):
    """Extract first keyword as statement type"""
    return tokens\[0]\[1]  # Returns "SELECT", "INSERT", etc.
```

**Purpose:** Determines which validation rules to apply

* SELECT → Check FROM clause
* INSERT → Check INTO and VALUES
* UPDATE → Check SET clause
* DELETE → Check FROM clause
* CREATE/DROP/ALTER → Check TABLE keyword

---

#### `parser/parser.py` - Validate Statement Structure

**Performs checks specific to each statement type:**

```
SELECT Validation:
├── Must have FROM clause
├── Must have columns before FROM (not empty)
└── Table must follow FROM

INSERT Validation:
├── Must have INTO clause
├── Must have VALUES/VALUE clause
├── INTO must come before VALUES
└── Table must follow INTO

UPDATE Validation:
├── Must have SET clause
└── Table must come before SET

DELETE Validation:
├── Must have FROM clause
└── Table must follow FROM

DDL (CREATE/DROP/ALTER) Validation:
├── Must have TABLE keyword
└── Table name must follow TABLE
```

**Example Error Detection:**

```sql
Input:  "SELECT FROM users;"
Error:  "Empty SELECT list" 
        "SELECT must specify columns or \* before FROM"

Input:  "INSERT INTO users VALUES (1);"
Output: No error (valid structure)

Input:  "INSERT VALUES (1) INTO users;"
Error:  "Invalid INSERT order"
        "INTO must come before VALUES"
```

---

### **3. Rules Engine** - Cross-Cutting Validation

#### `parser/rules.py` - Global SQL Rules

Applies syntax rules that apply to **all** SQL statements:

```python
1. Parentheses Matching:
   if sql.count("(") != sql.count(")"):
       Error: "Unmatched parentheses"

2. String Literal Validation:
   if sql.count("'") % 2 != 0:
       Error: "Unclosed string literal"

3. Subquery Nesting Depth:
   depth = count nested parentheses
   if depth > max\_depth:
       Error: "Subquery nested too deep"
```

**Depth Tracking Example:**

```sql
SELECT \* FROM (
    SELECT \* FROM (        ← Depth = 2
        SELECT \* FROM t    ← Depth = 3
    )
)
```

**Key Improvements Made:**
✅ Fixed: Error message formatting (removed trailing spaces)
✅ Improved: Code style and readability

---

### **4. Dialect Layer** - SQL Dialect-Specific Rules

#### Base Class: `dialect/base.py`

```python
class Dialect:
    def allowed\_statements(self) → List\[str]
    def max\_subquery\_depth(self) → int
    def forbidden\_keywords(self) → List\[str]
    def validate\_statement(stmt, tokens) → List\[Error]
    def validate\_clauses(stmt, tokens) → List\[Error]
    def validate\_ddl(stmt, tokens) → List\[Error]
```

#### `dialect/ansi.py` - ANSI SQL Dialect

```python
Allowed Statements:
├── SELECT, INSERT, UPDATE, DELETE
└── CREATE, DROP, ALTER

Max Nesting Depth: 2 levels
Forbidden Keywords:
├── LIMIT (PostgreSQL/MySQL specific)
├── TOP (SQL Server specific)
└── ILIKE (PostgreSQL specific)

Validation Rules:
└── Rejects any forbidden keywords with error message
```

**Example:**

```sql
Input:  "SELECT \* FROM users LIMIT 10;"
Error:  "LIMIT is not supported in ANSI SQL"
```

#### `dialect/mysql.py` - MySQL Dialect

```python
Allowed Statements:
├── SELECT, INSERT, UPDATE, DELETE
└── CREATE, DROP, ALTER

Max Nesting Depth: 4 levels (more permissive)
Forbidden Keywords: None (MySQL supports most)

Validation Rules:
└── LIMIT must be followed by a number
```

**Example:**

```sql
Input:  "SELECT \* FROM users LIMIT;"
Error:  "LIMIT must be followed by number"

Input:  "SELECT \* FROM users LIMIT 10;"
Valid:  No error
```

---

### **5. Error Handling** - `parser/errors.py`

```python
def error(line, issue, explanation):
    return {
        "line": line,
        "issue": issue,
        "explanation": explanation
    }
```

**Example Usage:**

```python
error(1, "Missing FROM clause", "SELECT must contain FROM")

# Output:
# {
#     "line": 1,
#     "issue": "Missing FROM clause",
#     "explanation": "SELECT must contain FROM"
# }
```

---

### **6. CLI Entry Point** - `cli/main.py`

**Main Processing Function:**

```python
def process(path, dialect\_name="ansi"):
    1. Load dialect (ANSI or MySQL)
    2. Read all queries from path
    3. FOR EACH query:
        a. Tokenize SQL string
        b. Apply rules engine checks
        c. Parse statement structure
        d. Apply dialect-specific checks
        e. Write JSON report
    4. Print summary statistics
```

**Key Improvements Made:**
✅ Better error handling with specific exceptions
✅ Added validation summary with pass/fail statistics
✅ Fixed dialect lookup with validation
✅ Separated statement type detection

**Example Output:**

```
============================================================
Validation Summary
============================================================
Total Queries: 4
✅ Passed: 2
❌ Failed: 2
============================================================
```

---

## 🔄 Processing Flow - Step by Step

Let's trace a real query through the entire system:

### **Query:** `SELECT \* FROM users;`

```
STEP 1: IO LAYER (reader.py)
┌─────────────────────────────────────────────────────┐
│ Input: inputs/test.txt                              │
│ Content: "SELECT \* FROM users;"                     │
│ Output: {                                           │
│   "source": "test.txt",                             │
│   "sql": "SELECT \* FROM users"                      │
│ }                                                   │
└─────────────────────────────────────────────────────┘
                      ↓
STEP 2: TOKENIZER (tokenizer.py)
┌─────────────────────────────────────────────────────┐
│ Input: "SELECT \* FROM users"                        │
│ Output: \[                                           │
│   ("KEYWORD", "SELECT", 1),                         │
│   ("STAR", "\*", 1),                                 │
│   ("KEYWORD", "FROM", 1),                           │
│   ("IDENTIFIER", "USERS", 1)                        │
│ ]                                                   │
└─────────────────────────────────────────────────────┘
                      ↓
STEP 3: STATEMENT TYPE (statement.py)
┌─────────────────────────────────────────────────────┐
│ Input: tokens\[0] = ("KEYWORD", "SELECT", 1)        │
│ Output: "SELECT"                                    │
│ → Routes to SELECT validation logic                │
└─────────────────────────────────────────────────────┘
                      ↓
STEP 4: RULES ENGINE (rules.py)
┌─────────────────────────────────────────────────────┐
│ Check 1: Parentheses match? ✅                      │
│ Check 2: String literals closed? ✅                │
│ Check 3: Nesting depth <= 2? ✅                    │
│ Output: \[] (no errors)                              │
└─────────────────────────────────────────────────────┘
                      ↓
STEP 5: PARSER (parser.py) - SELECT Checks
┌─────────────────────────────────────────────────────┐
│ Check 1: Has FROM clause? 
│   from\_idx = 2 ✅                                  │
│ Check 2: Has columns before FROM?
│   from\_idx (2) > 1? Yes ✅                         │
│ Check 3: Has table after FROM?
│   from\_idx + 1 (3) < len(tokens) (4)? Yes ✅     │
│ Output: \[] (no errors)                              │
└─────────────────────────────────────────────────────┘
                      ↓
STEP 6: DIALECT VALIDATION (ansi.py)
┌─────────────────────────────────────────────────────┐
│ Check 1: Is SELECT allowed in ANSI? Yes ✅         │
│ Check 2: Uses forbidden keywords?
│   ✅ No LIMIT, TOP, or ILIKE                       │
│ Output: \[] (no errors)                              │
└─────────────────────────────────────────────────────┘
                      ↓
STEP 7: OUTPUT (writer.py)
┌─────────────────────────────────────────────────────┐
│ Status: SUCCESS (no errors)                         │
│ File: outputs/query\_1.json                          │
│ Content: {                                          │
│   "q\_id": 1,                                        │
│   "source": "test.txt",                             │
│   "sql": "SELECT \* FROM users",                     │
│   "status": "SUCCESS",                              │
│   "errors": \[]                                      │
│ }                                                   │
└─────────────────────────────────────────────────────┘
```

---

## ❌ Error Detection Examples

### **Example 1: Empty SELECT List**

```sql
Input:  "SELECT FROM users;"

Tokenizer Output:
\[("KEYWORD", "SELECT", 1), ("KEYWORD", "FROM", 1), ("IDENTIFIER", "USERS", 1)]

Parser Check:
- from\_idx = 1
- Check: from\_idx <= 1? YES → ERROR

Output:
{
  "issue": "Empty SELECT list",
  "explanation": "SELECT must specify columns or \* before FROM"
}
```

### **Example 2: Unmatched Parentheses**

```sql
Input:  "SELECT \* FROM (SELECT id FROM users;"

Rules Engine:
- ( count: 2
- ) count: 1
- Not equal → ERROR

Output:
{
  "issue": "Unmatched parentheses",
  "explanation": "Number of ( and ) must be equal"
}
```

### **Example 3: INSERT Order Wrong**

```sql
Input:  "INSERT VALUES (1) INTO users;"

Parser Check for INSERT:
- INTO index: 3
- VALUES index: 1
- Check: into\_idx (3) > values\_idx (1)? YES → ERROR

Output:
{
  "issue": "Invalid INSERT order",
  "explanation": "INTO must come before VALUES"
}
```

### **Example 4: ANSI Dialect Violation**

```sql
Input:  "SELECT TOP 10 \* FROM users;"
Dialect: ANSI

Validation:
- Keywords: \[SELECT, TOP, \*, FROM, USERS]
- TOP in forbidden\_keywords? YES → ERROR

Output:
{
  "issue": "Non\_ANSI feature",
  "explanation": "TOP is not supported in ANSI SQL"
}
```

---

## 🐛 Bugs Fixed

### **Bug #1: Uninitialized Variable in INSERT Validation**

**Location:** `parser/parser.py` line 38

**Problem:**

```python
if 'VALUES' in keywords:
    values\_idx = \_find\_value\_idx(tokens, "VALUES")
elif 'VALUE' in keywords:
    values\_idx = \_find\_value\_idx(tokens, "VALUE")
# If neither condition is true, values\_idx is UNDEFINED!

if into\_idx == -1 or values\_idx == -1:  # NameError here!
```

**Fix:**

```python
values\_idx = -1  # Initialize before if/elif
if 'VALUES' in keywords:
    values\_idx = \_find\_value\_idx(tokens, "VALUES")
elif 'VALUE' in keywords:
    values\_idx = \_find\_value\_idx(tokens, "VALUE")
```

### **Bug #2: Incorrect File Parsing Logic**

**Location:** `io\_layer/reader.py` line 11

**Problem:**

```python
lines = \[line.strip() for line in content.splitlines()]
if len(lines) > 1:
    for line in lines:  # Treats each LINE as separate query!
        queries.append({"sql": line})
```

This treated each line as a separate query, breaking queries that span multiple lines.

**Fix:**

```python
raw\_queries = \[q.strip() for q in content.split(';') if q.strip()]
# Split by semicolon (SQL query delimiter), not by newlines
for query in raw\_queries:
    queries.append({"sql": query})
```

### **Bug #3: Escaped Quotes Not Handled**

**Location:** `parser/tokenizer.py` line 8

**Problem:**

```python
("STRING", r"'\[^']\*'")
# Regex pattern stops at FIRST quote, breaks on: 'John O'Brien'
```

**Fix:**

```python
("STRING", r"'(?:\[^'\\\\]|\\\\.)\*'")
# Handles: 'John O\\'Brien', 'Tab\\t', 'Newline\\n' etc.
```

### **Bug #4: Token Structure Changed (Tuple Size)**

**Location:** All files using tokens

**Problem:**
Tokenizer now returns 3-tuples `(type, value, line)` instead of 2-tuples.
All code extracting values needed updating.

**Fix:**

```python
# Old: for \_, v in tokens:
# New: for \_, v, \_ in tokens:  or  token\[1] for value
```

---

## 📊 Data Flow Summary

```
SQL Query File
    ↓
Reader: File → Queries
    ↓
For Each Query:
    ├─ Tokenizer: String → Tokens
    ├─ Statement Type: Determine query type
    ├─ Rules Engine: Global syntax checks
    ├─ Parser: Statement structure checks
    ├─ Dialect: Vendor-specific checks
    └─ Error List: Collect all errors
    ↓
Writer: Errors → JSON Report
    ↓
outputs/query\_N.json
```

---

## 🎯 Key Design Patterns Used

### **1. Layered Architecture**

* Separation of concerns
* Each layer has single responsibility
* Easy to modify one layer without affecting others

### **2. Strategy Pattern (Dialects)**

* `Dialect` base class defines interface
* `AnsiDialect` and `MySQLDialect` implement different strategies
* Client code uses dialect polymorphically

### **3. Decorator Pattern (Error Accumulation)**

* Each validation layer adds to error list
* Final error list contains all issues

### **4. Factory Pattern (Dialect Selection)**

```python
DIALECTS = {
    "ansi": AnsiDialect(),
    "mysql": MySQLDialect()
}
dialect = DIALECTS\[dialect\_name]
```

---

## 🚀 How to Add New Features

### **Add New Keyword**

1. Update `tokenizer.py` TOKENS regex

```python
("KEYWORD", r"\\b(SELECT|...|MYKEYWORD)\\b")
```

### **Add New Statement Type**

1. Add case in `parser.py`
2. Implement validation logic

### **Add New Dialect**

1. Create `dialect/newdialect.py`
2. Extend `Dialect` base class
3. Register in `DIALECTS` dict in `cli/main.py`

### **Add New Validation Rule**

1. Add check in `rules.py` (global rules)
2. Or add in corresponding `dialect/<name>.py` (dialect-specific)

---

## 📈 Testing \& Validation

**Test Files:** `inputs/test.txt`, `inputs/test1.txt`, `inputs/test2.txt`
**Output Files:** `outputs/query\_\*.json`

**Run Validation:**

```bash
python -m cli.main
```

**Check Results:**

```bash
ls outputs/  # See all generated reports
cat outputs/query\_1.json  # View specific report
```

---

## ✅ Summary

This is a **modular, extensible SQL validator** that:

* ✅ Tokenizes SQL correctly (including escaped strings)
* ✅ Validates statement structure
* ✅ Applies cross-cutting syntax rules
* ✅ Supports multiple SQL dialects
* ✅ Generates structured error reports
* ✅ Easy to extend with new dialects/rules

**Architecture:** Clean separation of concerns → Easy to test, debug, and extend!

