from parser.errors import error
from parser.statement import get_statement_type


def _find_value_idx(tokens, value):
    """Find index of token with given value. Tokens are now 3-tuples."""
    for i, token in enumerate(tokens):
        if token[1] == value:  # token[1] is the value
            return i
    return -1


def _find_all_indices(tokens, value):
    """Find all indices of tokens with given value."""
    indices = []
    for i, token in enumerate(tokens):
        if token[1] == value:
            indices.append(i)
    return indices


def _validate_select(tokens, sql=""):
    """Enhanced SELECT validation for complex queries."""
    errors = []
    line = 1
    
    from_idx = _find_value_idx(tokens, "FROM")
    if from_idx == -1:
        errors.append(error(line, "Missing FROM clause", "SELECT must contain FROM"))
    else:
        # Ensure there is at least one projection between SELECT and FROM
        if from_idx <= 1:
            errors.append(error(line, "Empty SELECT list", "SELECT must specify columns or * before FROM"))
        # Ensure a table/identifier follows FROM
        if from_idx + 1 >= len(tokens):
            errors.append(error(line, "Missing table", "FROM must be followed by a table or subquery"))
        else:
            # Check for invalid commas in FROM clause
            where_idx = _find_value_idx(tokens, "WHERE")
            join_idx = -1
            for join_kw in ["JOIN", "INNER", "LEFT", "RIGHT", "FULL", "CROSS"]:
                idx = _find_value_idx(tokens, join_kw)
                if idx != -1:
                    join_idx = idx
                    break
            
            end_idx = where_idx if where_idx != -1 else (join_idx if join_idx != -1 else len(tokens))
            
    
    # Check WHERE clause if present
    where_idx = _find_value_idx(tokens, "WHERE")
    if where_idx != -1 and where_idx + 1 >= len(tokens):
        errors.append(error(line, "Empty WHERE clause", "WHERE must be followed by a condition"))
    
    # Check GROUP BY if present
    group_idx = _find_value_idx(tokens, "GROUP")
    if group_idx != -1:
        if group_idx + 2 >= len(tokens) or tokens[group_idx + 1][1] != "BY":
            errors.append(error(line, "Invalid GROUP BY", "GROUP must be followed by BY"))
        elif group_idx + 2 >= len(tokens):
            errors.append(error(line, "Empty GROUP BY", "GROUP BY must specify columns"))
    
    # Check HAVING if present (only valid with GROUP BY)
    having_idx = _find_value_idx(tokens, "HAVING")
    if having_idx != -1:
        if group_idx == -1:
            errors.append(error(line, "Invalid HAVING", "HAVING requires GROUP BY"))
        elif having_idx + 1 >= len(tokens):
            errors.append(error(line, "Empty HAVING clause", "HAVING must be followed by a condition"))
    
    # Check ORDER BY if present
    order_idx = _find_value_idx(tokens, "ORDER")
    if order_idx != -1:
        if order_idx + 2 >= len(tokens) or tokens[order_idx + 1][1] != "BY":
            errors.append(error(line, "Invalid ORDER BY", "ORDER must be followed by BY"))
    
    # Check LIMIT if present
    limit_idx = _find_value_idx(tokens, "LIMIT")
    if limit_idx != -1 and limit_idx + 1 >= len(tokens):
        errors.append(error(line, "Empty LIMIT clause", "LIMIT must be followed by a number"))
    



def _validate_insert(tokens):
    """Enhanced INSERT validation."""
    errors = []
    line = 1
    
    into_idx = _find_value_idx(tokens, "INTO")
    values_idx = -1
    
    if 'VALUES' in [t[1] for t in tokens]:
        values_idx = _find_value_idx(tokens, "VALUES")
    elif 'VALUE' in [t[1] for t in tokens]:
        values_idx = _find_value_idx(tokens, "VALUE")
    
    if into_idx == -1 or values_idx == -1:
        errors.append(error(line, "Invalid INSERT", "INSERT must use INTO and VALUES/VALUE"))
    else:
        if into_idx > values_idx:
            errors.append(error(line, "Invalid INSERT order", "INTO must come before VALUES"))
        if into_idx + 1 >= len(tokens):
            errors.append(error(line, "Missing table", "INTO must be followed by a table name"))
        
        # Check for column list in parentheses after table
        if into_idx + 2 < len(tokens) and tokens[into_idx + 2][1] == "(":
            # Find matching closing paren
            paren_close_idx = -1
            paren_count = 0
            for i in range(into_idx + 2, len(tokens)):
                if tokens[i][1] == "(":
                    paren_count += 1
                elif tokens[i][1] == ")":
                    paren_count -= 1
                    if paren_count == 0:
                        paren_close_idx = i
                        break
            
            if paren_close_idx == -1:
                errors.append(error(line, "Unclosed parentheses", "Column list must be properly enclosed"))
        
        # Validate VALUES clause
        if values_idx + 1 < len(tokens) and tokens[values_idx + 1][1] != "(":
            errors.append(error(line, "Invalid VALUES", "VALUES must be followed by (...)"))
    
    return errors


def _validate_update(tokens):
    """Enhanced UPDATE validation."""
    errors = []
    line = 1
    
    set_idx = _find_value_idx(tokens, "SET")
    if set_idx == -1:
        errors.append(error(line, "Missing SET clause", "UPDATE must contain SET"))
    else:
        if set_idx <= 1:
            errors.append(error(line, "Missing table", "UPDATE must specify a table before SET"))
        elif set_idx + 1 >= len(tokens):
            errors.append(error(line, "Empty SET clause", "SET must be followed by column assignments"))
        
        # Check for WHERE clause
        where_idx = _find_value_idx(tokens, "WHERE")
        if where_idx != -1 and where_idx + 1 >= len(tokens):
            errors.append(error(line, "Empty WHERE clause", "WHERE must be followed by a condition"))
    
    return errors


def _validate_delete(tokens):
    """Enhanced DELETE validation."""
    errors = []
    line = 1
    
    from_idx = _find_value_idx(tokens, "FROM")
    if from_idx == -1:
        errors.append(error(line, "Missing FROM clause", "DELETE must use FROM"))
    else:
        if from_idx + 1 >= len(tokens):
            errors.append(error(line, "Missing table", "FROM must be followed by a table name"))
        
        # Check for WHERE clause
        where_idx = _find_value_idx(tokens, "WHERE")
        if where_idx != -1 and where_idx + 1 >= len(tokens):
            errors.append(error(line, "Empty WHERE clause", "WHERE must be followed by a condition"))
    
    return errors


def _validate_ddl(tokens):
    """Enhanced DDL (CREATE/DROP/ALTER) validation."""
    errors = []
    line = 1
    
    table_idx = _find_value_idx(tokens, "TABLE")
    if table_idx == -1:
        errors.append(error(line, "Invalid DDL", "DDL must specify TABLE"))
    else:
        if table_idx + 1 >= len(tokens):
            errors.append(error(line, "Missing table name", "TABLE must be followed by an identifier"))
        
        # Validate CREATE TABLE structure
        stmt_type = tokens[0][1] if tokens else ""
        if stmt_type == "CREATE" and table_idx + 2 < len(tokens):
            if tokens[table_idx + 2][1] == "(":
                # Find matching closing paren for column definitions
                paren_count = 0
                close_idx = -1
                for i in range(table_idx + 2, len(tokens)):
                    if tokens[i][1] == "(":
                        paren_count += 1
                    elif tokens[i][1] == ")":
                        paren_count -= 1
                        if paren_count == 0:
                            close_idx = i
                            break
                
                if close_idx == -1:
                    errors.append(error(line, "Unclosed table definition", "CREATE TABLE must have properly closed column definitions"))
                
                # Validate column definitions (basic check)
                col_def_tokens = tokens[table_idx + 3:close_idx]
                if not col_def_tokens:
                    errors.append(error(line, "Empty table definition", "CREATE TABLE must define at least one column"))
    
    return errors


def parse(sql, tokens):
    """Parse SQL query and validate syntax."""
    errors = []
    
    if not tokens:
        errors.append(error(1, "Empty query", "No SQL statement found"))
        return errors
    
    # Get statement type
    stmt = get_statement_type(tokens)
    
    if not stmt:
        errors.append(error(1, "Empty query", "No SQL statement found"))
        return errors
    

    
    # Route to appropriate validation function
    if stmt == "SELECT":
        errors.extend(_validate_select(tokens, sql))
    elif stmt == "INSERT":
        errors.extend(_validate_insert(tokens))
    elif stmt == "UPDATE":
        errors.extend(_validate_update(tokens))
    elif stmt == "DELETE":
        errors.extend(_validate_delete(tokens))
    elif stmt in ("CREATE", "DROP", "ALTER"):
        errors.extend(_validate_ddl(tokens))
    elif stmt in ("WITH", "UNION", "INTERSECT", "EXCEPT"):
        # Advanced query constructs are handled above
        pass
    else:
        errors.append(error(1, "Unsupported SQL", f"Statement type '{stmt}' is not yet supported"))
    
    return errors
