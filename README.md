# SQL Validator

A comprehensive **multi-dialect SQL query validation engine** that validates SQL queries against ANSI SQL and MySQL standards. Think of it as an **ESLint for SQL** - it tokenizes, parses, and validates SQL syntax with detailed error reporting.

## 🌟 Features

### Core Validation
- ✅ **Multi-dialect support**: ANSI SQL and MySQL
- ✅ **Statement support**: SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP
- ✅ **Complex queries**: JOINs, subqueries, CTEs, aggregations, set operations
- ✅ **Advanced clauses**: GROUP BY, HAVING, ORDER BY, WHERE, LIMIT, OFFSET
- ✅ **Aggregate functions**: COUNT, SUM, AVG, MIN, MAX, and 10+ more
- ✅ **JOIN types**: INNER, LEFT, RIGHT, FULL, CROSS with ON clause validation
- ✅ **Set operations**: UNION, INTERSECT, EXCEPT

### Comprehensive Syntax Checking
- ✅ Unmatched/unclosed parentheses
- ✅ Unclosed string and identifier literals
- ✅ Empty clauses (empty SELECT list, WHERE, GROUP BY, etc.)
- ✅ Missing mandatory keywords and clauses
- ✅ Invalid clause ordering
- ✅ Subquery nesting depth validation
- ✅ Dangling operators (leading/trailing)
- ✅ Empty IN/VALUES lists
- ✅ Unmatched CASE/END statements
- ✅ Aggregate function validation
- ✅ DISTINCT placement checking
- ✅ Column alias (AS) validation

### Output
- 📄 **JSON Reports**: Detailed error reports for each query
- 📊 **Summary Statistics**: Total, passed, and failed query counts
- 🎯 **Error Details**: Line numbers, issue type, and explanations

---

## 📋 Requirements

- **Python**: 3.8+
- **Dependencies**: None (pure Python implementation)

---

## 🚀 Quick Start

### 1. Clone/Setup the Project

```bash
git clone <repository-url>
cd sqlvalidator
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 2. Run the Validator

```bash
# Validate all SQL files in the inputs directory
python -m cli.main inputs

# Validate a single SQL file
python -m cli.main inputs/test_001_create.txt

# Validate with MySQL dialect
python -m cli.main inputs --dialect mysql

# Show help
python -m cli.main --help
```

---

## 📖 Usage Guide

### Command-Line Interface

The CLI accepts **required file path** and **optional dialect** arguments:

```bash
python -m cli.main PATH [--dialect {ansi,mysql}]
```

#### Required Arguments
- **PATH**: File or directory path containing SQL files

#### Optional Arguments
- **--dialect, -d**: SQL dialect (ansi, mysql) - default: ansi

### Examples

```bash
# Validate directory with ANSI dialect (default)
python -m cli.main inputs

# Validate directory with explicit ANSI dialect
python -m cli.main inputs --dialect ansi

# Validate directory with MySQL dialect
python -m cli.main inputs --dialect mysql
python -m cli.main inputs -d mysql

# Validate single file
python -m cli.main inputs/test_022_select.txt

# Validate single file with MySQL dialect
python -m cli.main inputs/test_001_create.txt --dialect mysql

# Display help
python -m cli.main --help
```

### Output Example

```
============================================================
Validation Summary
============================================================
Total Queries: 15
✅ Passed: 14
❌ Failed: 1
============================================================
```

JSON reports are generated in the `outputs/` directory:

```json
{
    "q_id": 1,
    "source": "test_001_create.txt",
    "sql": "CREATE TABLE employees (...)",
    "status": "SUCCESS",
    "errors": []
}
```

---

## 🎯 Supported SQL Statements

**DML**: SELECT, INSERT, UPDATE, DELETE  
**DDL**: CREATE TABLE, DROP TABLE, ALTER TABLE  
**Features**: JOINs, Subqueries, CTEs, GROUP BY, HAVING, ORDER BY, UNION, INTERSECT, EXCEPT, Aggregate Functions

For detailed syntax examples and validation rules, see [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md).

---

## 🏗️ Architecture

See [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md) for detailed architecture documentation and module descriptions.

---

## 📊 Output Format

### JSON Report Structure

Each query generates a JSON file (`outputs/query_N.json`):

```json
{
    "q_id": 1,
    "source": "test_001_create.txt",
    "sql": "CREATE TABLE employees (...)",
    "status": "SUCCESS|FAILED",
    "errors": [
        {
            "line": 1,
            "issue": "Issue Title",
            "explanation": "Detailed explanation of the issue"
        }
    ]
}
```

### Console Summary

After validation completes, a summary is displayed:

```
============================================================
Validation Summary
============================================================
Total Queries: 15
✅ Passed: 14
❌ Failed: 1
============================================================
```

---

## 📝 Example Queries

### Valid SQL
```sql
SELECT id, name FROM users;

SELECT e.dept_id, COUNT(*) FROM employees e
GROUP BY e.dept_id HAVING COUNT(*) > 5
ORDER BY e.dept_id;

SELECT * FROM orders 
WHERE customer_id IN (SELECT id FROM customers)
UNION
SELECT * FROM archived_orders;
```

### Invalid SQL (Will Fail)
```sql
SELECT id, name;  -- Missing FROM clause

SELECT * FROM users WHERE id = (1;  -- Unmatched parentheses

SELECT FROM users;  -- Empty SELECT list
```

---

## 📚 Documentation

For more detailed information, see:
- [CLI_USAGE.md](CLI_USAGE.md) - Detailed CLI usage examples
- [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md) - Architecture and technical details
- [requirements.md](requirements.md) - Functional requirements
- [design.md](design.md) - Design decisions
- [STUDENT_GUIDE.md](STUDENT_GUIDE.md) - Learning guide

---

## 📄 License

This project is part of the BluePineapple SQL learning initiative.

---

## 📞 Support

For issues or questions, please refer to the documentation files listed above.
