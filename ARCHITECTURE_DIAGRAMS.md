# SQL Validator - Architecture Diagrams

## 1\. System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                            │
│                      python -m cli.main                             │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CLI LAYER (cli/main.py)                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ process(path, dialect\\\\\\\\\\\\\\\_name)                                 │   │
│  │ - Load dialect (ANSI or MySQL)                               │   │
│  │ - Read queries from path                                     │   │
│  │ - Orchestrate validation pipeline                            │   │
│  │ - Print summary statistics                                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
        │                      │                      │
        ▼                      ▼                      ▼
  ┌──────────────┐    ┌─────────────────┐    ┌──────────────────┐
  │  IO LAYER    │    │ PARSING LAYER   │    │  DIALECT LAYER   │
  ├──────────────┤    ├─────────────────┤    ├──────────────────┤
  │ reader.py    │    │ tokenizer.py    │    │  base.py         │
  │ - Read files │    │ - String→tokens │    │  ansi.py         │
  │ - Split `;`  │    │ - Line tracking │    │  mysql.py        │
  │              │    │ - Regex match   │    │ - Rules \& checks │
  │ writer.py    │    │                 │    │                  │
  │ - Write JSON │    │ statement.py    │    │ Provides:        │
  │ - Format out │    │ - Get stmt type │    │ - Allowed stmts  │
  │              │    │                 │    │ - Max nesting    │
  │              │    │ parser.py       │    │ - Forbidden keys │
  │              │    │ - Validate DML  │    │                  │
  │              │    │ - Validate DDL  │    │                  │
  │              │    │                 │    │                  │
  │              │    │ rules.py        │    │                  │
  │              │    │ - Parentheses   │    │                  │
  │              │    │ - String check  │    │                  │
  │              │    │ - Nesting depth │    │                  │
  │              │    │                 │    │                  │
  │              │    │ errors.py       │    │                  │
  │              │    │ - Error format  │    │                  │
  └──────────────┘    └─────────────────┘    └──────────────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │   ERROR COLLECTION  │
                    │  (List of errors)   │
                    └─────────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │   OUTPUT (JSON)     │
                    │  outputs/query\\\_N   │
                    │       .json         │
                    └─────────────────────┘
```

---

## 2\. Data Transformation Pipeline

```
Input Query
"SELECT \* FROM users WHERE id = 1"
          │
          ▼
     TOKENIZER
     (tokenizer.py)
          │
          ├─ Regex matching
          ├─ Case conversion
          ├─ Line number tracking
          │
          ▼
   Token Stream
   \[
     ("KEYWORD", "SELECT", 1),
     ("STAR", "\*", 1),
     ("KEYWORD", "FROM", 1),
     ("IDENTIFIER", "USERS", 1),
     ("KEYWORD", "WHERE", 1),
     ("IDENTIFIER", "ID", 1),
     ("OPERATOR", "=", 1),
     ("NUMBER", "1", 1)
   ]
          │
    ┌─────┴─────┬─────────────┬──────────────┐
    ▼           ▼             ▼              ▼
 RULES       PARSER      STATEMENT      DIALECT
(rules.py)  (parser.py) (statement.py) (dialect/\*.py)
    │           │            │             │
    │           │            │             │
    ├─ ()       ├─ SELECT    ├─ Extract    ├─ ANSI 
    │ match     │ checks     │ stmt type   │ compatibility
    │           │            │ "SELECT"    │
    ├─ ''       ├─ INSERT    └────────┐    ├─ MySQL
    │ literals  │ checks              │    │ compatibility
    │           │                     │    │
    ├─ Nesting  ├─ UPDATE             │    └─ Custom
    │ depth     │ checks              │      validations
    │           │                     │
    └─ All      ├─ DELETE             │
       errors   │ checks              │
                │                     │
                ├─ CREATE/DROP/ALTER  │   
                │ checks              │
                │                     │
                └─────────────────────┘
                         │
                         ▼
                 Combined Error List
                   \[Error, Error, ...]
                         │
                         ▼
                   JSON Report
               {
                 "q\_id": 1,
                 "status": "FAILED",
                 "errors": \[...]
               }
```

---

## 3\. Token Type Classification

```
SQL Lexicon
├─ KEYWORDS (Reserved Words)
│  ├─ DML: SELECT, INSERT, UPDATE, DELETE
│  ├─ DDL: CREATE, DROP, ALTER
│  ├─ Clauses: FROM, WHERE, INTO, VALUES, SET, TABLE
│  └─ Operators: IN, LIMIT
│
├─ IDENTIFIERS (Names)
│  ├─ Tables: users, products
│  ├─ Columns: id, name, email
│  └─ Aliases: u (FROM users u)

│
├─ LITERALS (Data Values)
│  ├─ Numbers: 123, 45.67
│  ├─ Strings: 'John', 'O\\\\\\\\\\\\\\\\'Brien'
│  └─ Special: \\\\\\\\\\\\\\\* (SELECT \\\\\\\\\\\\\\\*)
│
├─ OPERATORS
│  ├─ Comparison: =, <, >, <=, >=, !=
│  └─ Logical: AND, OR, NOT
│
└─ SYMBOLS (Punctuation)
   ├─ Parentheses: (, )
   ├─ Separators: ,
   └─ Terminator: ;
```

---

## 4\. Validation Pipeline Sequence

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. RULES ENGINE (Global Checks)                                 │
│    ├─ Parentheses: count('(') == count(')')  \[Line 6]           │
│    ├─ Strings: count("'") is even            \[Line 10]          │
│    └─ Nesting: max\_depth <= allowed          \[Line 15]          │
│    ║                                                            │
│    ║ Output: errors\[]                                           │
└─────────────────────────────────────────────────────────────────┘
                          ║
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. PARSER (Statement Structure)                                 │
│    (Only if statement type identified)                          │
│    ├─ SELECT Validator:                                         │
│    │  ├─ Find FROM clause (required)                            │
│    │  ├─ Check for columns between SELECT and FROM              │
│    │  └─ Ensure table after FROM                                │
│    ├─ INSERT Validator:                                         │
│    │  ├─ Find INTO clause                                       │
│    │  ├─ Find VALUES/VALUE clause                               │
│    │  ├─ Verify order: INTO before VALUES                       │
│    │  └─ Ensure table after INTO                                │
│    ├─ UPDATE Validator:                                         │
│    │  ├─ Find SET clause (required)                             │
│    │  └─ Ensure table before SET                                │
│    ├─ DELETE Validator:                                         │
│    │  ├─ Find FROM clause (required)                            │
│    │  └─ Ensure table after FROM                                │
│    └─ DDL Validator (CREATE/DROP/ALTER):                        │
│       ├─ Find TABLE keyword                                     │
│       └─ Ensure name after TABLE                                │
│                                                                 │
│    Output: errors\[]                                             │
└─────────────────────────────────────────────────────────────────┘
                          ║
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. DIALECT VALIDATION                                           │
│    ├─ Statement Allowed?                                        │
│    │  └─ Check against allowed\\\\\\\\\\\\\\\_statements()              │
│    ├─ Forbidden Keywords?                                       │
│    │  └─ Check against forbidden\\\\\\\\\\\\\\\_keywords()              │
│    ├─ Clause-specific Rules?                                    │
│    │  ├─ ANSI: Rejects LIMIT, TOP, ILIKE                        │
│    │  └─ MySQL: LIMIT must have number after it                 │
│    └─ DDL Rules?                                                │
│       └─ (Extensible for future rules)                          │
│                                                                 │
│    Output: errors\[]                                             │
└─────────────────────────────────────────────────────────────────┘
                          ║
                          ▼
           ┌──────────────────────────────┐
           │ COMBINE ALL ERRORS           │
           │ Total errors from all layers │
           └──────────────────────────────┘
                          ║
                          ▼
           ┌──────────────────────────────┐
           │ DETERMINE STATUS             │
           │ errors? → FAILED : SUCCESS   │
           └──────────────────────────────┘
                          ║
                          ▼
           ┌──────────────────────────────┐
           │ WRITE JSON REPORT            │
           │ outputs/query\_n.json         │
           └──────────────────────────────┘
```

---

## 5\. Token Structure Evolution

```
OLD (Before Fix):
TOKENS: \\\\\\\\\\\\\\\[("KEYWORD", "SELECT"), ("IDENTIFIER", "USERS")]
              │            │
              │            └─ value
              └─ type
Problem: No line info for error reporting

NEW (After Fix):
TOKENS: \\\\\\\\\\\\\\\[("KEYWORD", "SELECT", 1), ("IDENTIFIER", "USERS", 1)]
              │            │        │
              │            │        └─ line number
              │            └─ value
              └─ type
Benefit: Can report "line 1" in error messages
```

---

## 6\. Error Propagation Flow

```
Query: "INSERT VALUES (1) INTO users;"

TOKENIZER
└─ Tokens: \\\\\\\\\\\\\\\[INSERT, VALUES, ..., INTO, ...]
   └─ No errors

RULES ENGINE
├─ Parentheses: 1 (, 1 ) ✓
├─ Strings: even count ✓
├─ Nesting: depth ✓
└─ errors = \\\\\\\\\\\\\\\[]

PARSER (INSERT validation)
├─ Find INTO: found at index 3 ✓
├─ Find VALUES: found at index 1 ✓
├─ Check order: into\\\\\\\\\\\\\\\_idx (3) > values\\\\\\\\\\\\\\\_idx (1)?
│  YES! ✗ → error\\\\\\\\\\\\\\\["Invalid INSERT order"]
├─ Check table after INTO: skipped (failed earlier)
└─ errors = \\\\\\\\\\\\\\\[{"issue": "Invalid INSERT order", ...}]

DIALECT
├─ Is INSERT allowed? ✓
├─ Forbidden keywords? ✓
└─ errors = \\\\\\\\\\\\\\\[] (no new errors)

FINAL
errors = \\\\\\\\\\\\\\\[
  {"issue": "Invalid INSERT order", ...}
]
status = "FAILED"
```

---

## 7\. Class Hierarchy

```
Dialect (Abstract Base)
├─ method: allowed\\\\\\\\\\\\\\\_statements()
├─ method: max\\\\\\\\\\\\\\\_subquery\\\\\\\\\\\\\\\_depth()
├─ method: forbidden\\\\\\\\\\\\\\\_keywords()
├─ method: validate\\\\\\\\\\\\\\\_statement()
├─ method: validate\\\\\\\\\\\\\\\_clauses()
└─ method: validate\\\\\\\\\\\\\\\_ddl()
   │
   ├─ AnsiDialect
   │  ├─ allowed: SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER
   │  ├─ forbidden: LIMIT, TOP, ILIKE
   │  └─ max\\\\\\\\\\\\\\\_depth: 2
   │
   └─ MySQLDialect
      ├─ allowed: SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER
      ├─ forbidden: none
      ├─ max\\\\\\\\\\\\\\\_depth: 4
      └─ special: validates LIMIT syntax
```

---

## 8\. File Read/Write Operations

```
INPUT
  ↓
inputs/
├─ test.txt
│  └─ Query 1; Query 2; Query 3;
├─ test1.txt
│  └─ Query 4;
└─ test2.txt
   └─ Query 5;
  ↓
READER (reader.py)
├─ read\\\\\\\\\\\\\\\_input(path)
│  ├─ Is directory? → read all files
│  ├─ Is file? → read single file
│  └─ Extract queries (split by ';')
  ↓
  \\\\\\\\\\\\\\\[
    {source: "test.txt", sql: "Query 1"},
    {source: "test.txt", sql: "Query 2"},
    {source: "test.txt", sql: "Query 3"},
    {source: "test1.txt", sql: "Query 4"},
    {source: "test2.txt", sql: "Query 5"}
  ]
  ↓
VALIDATION (multiple layers)
  ↓
  \\\\\\\\\\\\\\\[
    {q\\\\\\\\\\\\\\\_id: 1, status: "SUCCESS", errors: \\\\\\\\\\\\\\\[]},
    {q\\\\\\\\\\\\\\\_id: 2, status: "FAILED", errors: \\\\\\\\\\\\\\\[...]},
    {q\\\\\\\\\\\\\\\_id: 3, status: "SUCCESS", errors: \\\\\\\\\\\\\\\[]},
    {q\\\\\\\\\\\\\\\_id: 4, status: "FAILED", errors: \\\\\\\\\\\\\\\[...]},
    {q\\\\\\\\\\\\\\\_id: 5, status: "SUCCESS", errors: \\\\\\\\\\\\\\\[]}
  ]
  ↓
WRITER (writer.py)
├─ write\\\\\\\\\\\\\\\_json\\\\\\\\\\\\\\\_report(n, src, sql, status, errors)
  ↓
outputs/
├─ query\\\\\\\\\\\\\\\_1.json
├─ query\\\\\\\\\\\\\\\_2.json
├─ query\\\\\\\\\\\\\\\_3.json
├─ query\\\\\\\\\\\\\\\_4.json
└─ query\\\\\\\\\\\\\\\_5.json
```

---

## 9\. Error Message Structure

```json
{
  "q\\\\\\\\\\\\\\\_id": 1,
  "source": "test.txt",
  "sql": "SELECT FROM users",
  "status": "FAILED",
  "errors": \\\\\\\\\\\\\\\[
    {
      "line": 1,
      "issue": "Empty SELECT list",
      "explanation": "SELECT must specify columns or \\\\\\\\\\\\\\\* before FROM"
    }
  ]
}
```

**Error Elements:**

* `line`: Line number where error occurred
* `issue`: Short error title (1-3 words)
* `explanation`: Full description of the problem

---

## 10\. Decision Tree for Statement Validation

```
Query Received
│
├─ RULES CHECKS (Always)
│  ├─ Parentheses balanced?
│  ├─ Strings closed?
│  └─ Nesting depth OK?
│
├─ Get Statement Type
│  │
│  ├─ SELECT?
│  │  ├─ Has FROM?
│  │  ├─ Has columns?
│  │  └─ Table after FROM?
│  │
│  ├─ INSERT?
│  │  ├─ Has INTO?
│  │  ├─ Has VALUES/VALUE?
│  │  ├─ INTO before VALUES?
│  │  └─ Table after INTO?
│  │
│  ├─ UPDATE?
│  │  ├─ Has SET?
│  │  └─ Table before SET?
│  │
│  ├─ DELETE?
│  │  ├─ Has FROM?
│  │  └─ Table after FROM?
│  │
│  ├─ CREATE/DROP/ALTER?
│  │  ├─ Has TABLE?
│  │  └─ Name after TABLE?
│  │
│  └─ Unknown?
│     └─ "Unsupported SQL"
│
├─ DIALECT VALIDATION
│  ├─ Statement allowed?
│  ├─ Forbidden keywords?
│  ├─ Clause rules (LIMIT, etc.)?
│  └─ DDL rules?
│
└─ RESULT
   ├─ Errors found? → FAILED
   └─ No errors? → SUCCESS
```

This comprehensive visual guide shows:

* ✅ How data flows through the system
* ✅ How each layer processes input
* ✅ Error collection and aggregation
* ✅ Output formatting and reporting
