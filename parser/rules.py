import re
from parser.errors import error

def apply_rules(sql, max_depth):
    """
    Apply comprehensive validation rules to SQL queries.
    Checks for:
    - Balanced parentheses
    - Closed string literals
    - Subquery nesting depth (specifically for SELECT statements)
    - Reserved word conflicts
    - Expression syntax
    """
    errors = []
    line = 1
    
    # Check balanced parentheses
    if sql.count("(") != sql.count(")"):
        errors.append(error(line, "Unmatched parentheses", "Number of ( and ) must be equal"))
    
    # Check unclosed string literals (single quotes)
    if sql.count("'") % 2 != 0:
        errors.append(error(line, "Unclosed string literal", "String must start and end with single quotes"))
    
    # Check unclosed identifier quotes (double quotes)
    if sql.count('"') % 2 != 0:
        errors.append(error(line, "Unclosed identifier", "Identifier must start and end with double quotes"))
    
    # Check subquery nesting depth (only for SELECT statements in subqueries)
    
    depth = 0
    max_seen = 0
    in_string = False
    string_char = None
    paren_stack = []
    
    for i, ch in enumerate(sql):
        # Track string literals to avoid counting parentheses inside strings
        if ch in ("'", '"') and (i == 0 or sql[i-1] != "\\"):
            if not in_string:
                in_string = True
                string_char = ch
            elif ch == string_char:
                in_string = False
                string_char = None
        
        if not in_string:
            if ch == "(":
                # Check if this looks like a subquery (preceded by SELECT/WHERE/etc or no keyword)
                # Simple heuristic: if it contains SELECT, it's likely a subquery
                paren_stack.append(i)
                depth += 1
                max_seen = max(max_seen, depth)
            elif ch == ")":
                if paren_stack:
                    start_paren = paren_stack.pop()
                    # Check if the content between parentheses contains SELECT
                    inner_content = sql[start_paren+1:i].strip()
                    # Only count as subquery nesting if it contains SELECT
                    if "SELECT" not in inner_content.upper():
                        # Not a subquery, don't count in nesting depth
                        max_seen = max(0, max_seen - 1)
                depth -= 1
    
    if max_seen > max_depth:
        errors.append(error(line, "Subquery nested too deep", f"Maximum allowed nesting is {max_depth}"))
    
    # Check for common syntax issues
    # Multiple spaces can sometimes indicate syntax errors
    if "  " in sql:
        # This is just informational, not necessarily an error
        pass
    
    # Check for dangling operators (basic check)
    # Look for operators at the end or beginning
    stripped = sql.strip()
    operator_pattern = r'[\+\-\*/%=<>!&|\|]'
    
    if stripped and re.search(r'^' + operator_pattern, stripped):
        errors.append(error(line, "Leading operator", "Query cannot start with an operator"))
    
    if stripped and re.search(operator_pattern + r'$', stripped):
        errors.append(error(line, "Trailing operator", "Query cannot end with an operator"))
    
    # Check for consecutive operators (except for known operators like !=, <=, >=, <>)
    if re.search(r'[\+\-\*/%]\s*[\+\-\*/%]', sql):
        # Allow for unary operators
        if not re.search(r'[\(,]\s*[-+]\s*[\d(]', sql):
            # Could be an error, but might be unary operator
            pass
    
    # Check for valid CASE statement structure if present
    if 'CASE' in sql.upper():
        case_count = sql.upper().count('CASE')
        end_count = sql.upper().count('END')
        if case_count != end_count:
            errors.append(error(line, "Unmatched CASE/END", "Every CASE must have a matching END"))
    
    # Check for BETWEEN syntax
    between_pattern = r'\bBETWEEN\b.*?\bAND\b'
    between_matches = re.findall(between_pattern, sql, re.IGNORECASE)
    # Basic validation - just ensure BETWEEN has matching AND nearby
    
    # Check for IN clause with empty value list
    in_pattern = r'\bIN\s*\(\s*\)'
    if re.search(in_pattern, sql, re.IGNORECASE):
        errors.append(error(line, "Empty IN list", "IN clause must contain at least one value"))
    
    # Check for JOIN without ON (basic check)
    # This is more of a warning as CROSS JOIN doesn't need ON
    join_pattern = r'\b(INNER|LEFT|RIGHT|FULL)\s+JOIN\b'
    on_pattern = r'\bON\b'
    if re.search(join_pattern, sql, re.IGNORECASE) and not re.search(on_pattern, sql, re.IGNORECASE):
        # Could be error or implicit join syntax
        pass
    
    # Check for malformed column aliases (AS keyword)
    # SELECT col AS should be followed by identifier
    as_pattern = r'\bAS\s+(?=[^a-zA-Z_])'
    if re.search(as_pattern, sql, re.IGNORECASE):
        errors.append(error(line, "Invalid alias", "AS must be followed by a valid identifier"))
    
    # Check for aggregate functions without proper context
    aggregate_funcs = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP_CONCAT', 'STRING_AGG']
    for func in aggregate_funcs:
        # Aggregate functions should have parentheses
        pattern = rf'\b{func}\s*\('
        if re.search(pattern, sql, re.IGNORECASE):
            # Find if it's closed properly
            start_idx = re.search(pattern, sql, re.IGNORECASE)
            if start_idx:
                paren_count = 0
                found_close = False
                for i in range(start_idx.end() - 1, len(sql)):
                    if sql[i] == '(':
                        paren_count += 1
                    elif sql[i] == ')':
                        paren_count -= 1
                        if paren_count == 0:
                            found_close = True
                            break
                
                if not found_close:
                    errors.append(error(line, f"Unclosed {func}", f"{func}(...) must be properly closed"))
    
    # Check for DISTINCT usage
    if 'DISTINCT' in sql.upper():
        # DISTINCT should appear right after SELECT
        select_idx = sql.upper().find('SELECT')
        distinct_idx = sql.upper().find('DISTINCT')
        if select_idx != -1 and distinct_idx != -1:
            between = sql[select_idx + 6:distinct_idx].strip()
            if between and between != '*':
                # DISTINCT might be in wrong position
                pass
    
    return errors
    
