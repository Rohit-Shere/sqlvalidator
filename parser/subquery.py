"""
Enhanced subquery validation module.
Handles validation of nested SELECT statements, CTEs, and complex query structures.
"""

from parser.errors import error


def extract_subqueries(sql):
    """
    Extract all subqueries from SQL statement.
    Returns list of (start_idx, end_idx, subquery_sql) tuples.
    """
    subqueries = []
    paren_stack = []
    in_string = False
    string_char = None
    
    for i, ch in enumerate(sql):
        # Handle string literals
        if ch == "'" and (i == 0 or sql[i-1] != "\\"):
            in_string = not in_string
            string_char = ch if not in_string else None
        
        if not in_string:
            if ch == "(":
                paren_stack.append(i)
            elif ch == ")":
                if paren_stack:
                    start = paren_stack.pop()
                    # Check if this looks like a subquery (contains SELECT)
                    potential_subquery = sql[start+1:i].strip()
                    if potential_subquery.upper().startswith("SELECT"):
                        subqueries.append((start, i, potential_subquery))
    
    return subqueries


def validate_subquery_syntax(subquery_sql):
    """Validate syntax of a single subquery."""
    errors = []
    
    if not subquery_sql.strip():
        errors.append(error(1, "Empty subquery", "Subquery cannot be empty"))
        return errors
    
    # Check that subquery is a SELECT statement
    if not subquery_sql.strip().upper().startswith("SELECT"):
        errors.append(error(1, "Invalid subquery", "Subquery must be a SELECT statement"))
        return errors
    
    # Check for unmatched parentheses
    if subquery_sql.count("(") != subquery_sql.count(")"):
        errors.append(error(1, "Unmatched parentheses in subquery", 
                          "Subquery has unbalanced parentheses"))
    
    # Check for unclosed strings
    if subquery_sql.count("'") % 2 != 0:
        errors.append(error(1, "Unclosed string in subquery", 
                          "Subquery has unclosed string literal"))
    
    return errors


def validate_subquery_context(sql, subqueries, nested_level=0):
    """
    Validate that subqueries are in valid contexts.
    Checks:
    - Subqueries in FROM clause
    - Subqueries in WHERE clause  
    - Subqueries in SELECT list (scalar subqueries)
    - Nesting depth
    """
    errors = []
    
    if nested_level > 3:
        errors.append(error(1, "Excessive subquery nesting", 
                          "Nesting more than 3 levels deep is not recommended"))
    
    for start_idx, end_idx, subq_sql in subqueries:
        # Validate the subquery itself
        errors.extend(validate_subquery_syntax(subq_sql))
        
        # Check context - what comes before the subquery
        if start_idx > 0:
            before = sql[:start_idx].strip().upper()
            
            # Check if context is valid
            valid_contexts = ["FROM", "WHERE", "IN", "EXISTS", "NOT"]
            has_valid_context = any(before.endswith(ctx) for ctx in valid_contexts)
            
            # Also check if it's in SELECT list
            select_idx = sql.upper().find("SELECT")
            from_idx = sql.upper().find("FROM", select_idx)
            if select_idx != -1 and from_idx == -1:
                # Might be in SELECT list before FROM
                has_valid_context = True
            elif select_idx != -1 and from_idx != -1:
                if select_idx < start_idx < from_idx:
                    # In SELECT list before FROM
                    has_valid_context = True
            
            if not has_valid_context and "SELECT" in before:
                # Might be in a JOIN ON condition or other valid location
                # This is more permissive to avoid false positives
                pass
        
        # Recursively check nested subqueries
        nested_subqueries = extract_subqueries(subq_sql)
        if nested_subqueries:
            errors.extend(validate_subquery_context(subq_sql, nested_subqueries, nested_level + 1))
    
    return errors


def validate_cte(sql):
    """
    Validate Common Table Expression (WITH clause) syntax.
    WITH cte_name AS (SELECT ...) SELECT ...
    """
    errors = []
    
    if not sql.strip().upper().startswith("WITH"):
        return errors
    
    # Find the WITH clause
    with_idx = sql.upper().find("WITH")
    as_idx = sql.upper().find("AS", with_idx)
    
    if as_idx == -1:
        errors.append(error(1, "Invalid CTE", "WITH clause must include AS (SELECT ...)"))
        return errors
    
    # Extract CTE name (between WITH and AS)
    cte_name = sql[with_idx + 4:as_idx].strip()
    if not cte_name or " " in cte_name or "(" in cte_name:
        errors.append(error(1, "Invalid CTE name", 
                          "CTE name must be a valid identifier between WITH and AS"))
    
    # Check for SELECT statement after AS
    after_as = sql[as_idx + 2:].strip()
    if not after_as.startswith("("):
        errors.append(error(1, "Invalid CTE syntax", 
                          "AS must be followed by (SELECT ...)"))
    
    return errors


def validate_union_queries(sql):
    """
    Validate UNION, INTERSECT, EXCEPT clause syntax.
    Both sides must be SELECT statements.
    """
    errors = []
    
    for set_op in ["UNION", "INTERSECT", "EXCEPT"]:
        if set_op in sql.upper():
            parts = sql.upper().split(set_op)
            if len(parts) != 2:
                errors.append(error(1, f"Multiple {set_op}s", 
                              f"Ensure {set_op} syntax is correct. Found {len(parts)-1} {set_op} operations"))
            
            # Check both parts are SELECT
            for i, part in enumerate(parts):
                clean_part = part.strip()
                if not clean_part.startswith("SELECT") and i > 0:
                    errors.append(error(1, f"Invalid {set_op}", 
                                  f"Both sides of {set_op} must be SELECT statements"))
    
    return errors
