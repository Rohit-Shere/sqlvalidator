# SQL Validator CLI - Usage Guide

The SQL Validator can now be executed with command-line arguments to specify the SQL file/directory path and the SQL dialect.

## Required Argument

**PATH** - The path to a SQL file or directory containing SQL files

## Optional Arguments

**--dialect, -d** - SQL dialect to validate against
- Available options: `ansi` (default), `mysql`

## Usage Examples

### Validate all files in a directory (default: ANSI dialect)
```bash
python -m cli.main inputs
```

### Validate all files in a directory with ANSI dialect (explicit)
```bash
python -m cli.main inputs --dialect ansi
```

### Validate with MySQL dialect
```bash
python -m cli.main inputs --dialect mysql
python -m cli.main inputs -d mysql
```

### Validate a single file
```bash
python -m cli.main inputs/test_022_select.txt
```

### Validate a single file with MySQL dialect
```bash
python -m cli.main inputs/test_001_create.txt --dialect mysql
```

### Display help and available options
```bash
python -m cli.main --help
python -m cli.main -h
```

## Output

The validator generates:
1. **Console output** - A summary of validation results showing:
   - Total queries validated
   - Number of passed queries
   - Number of failed queries

2. **JSON Reports** - Individual JSON files in the `outputs/` directory for each query

## Error Handling

- If the specified path does not exist, an error message will be displayed:
  ```
  Error: Path does not exist: invalid_path
  ```

- If an invalid dialect is specified, the application will show available dialects and exit with an error.

## Example Execution

```bash
$ python -m cli.main inputs --dialect ansi
============================================================
Validation Summary
============================================================
Total Queries: 15
Passed: 14
Failed: 1
============================================================
```
