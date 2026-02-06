from parser.errors import error
from parser.statement import get_statement_type


def _find_value_idx(tokens, value):
    for i, (_, v) in enumerate(tokens):
        if v == value:
            return i
    return -1


def parse(sql, tokens):
    errors = []
    line = 1
    stmt = get_statement_type(tokens)
    keywords = [v for _, v in tokens]

    if not stmt:
        errors.append(error(line, "Empty query", "No SQL statement found"))
        return errors

    # SELECT checks
    if stmt == "SELECT":
        from_idx = _find_value_idx(tokens, "FROM")
        if from_idx == -1:
            errors.append(error(line, "Missing FROM clause", "SELECT must contain FROM"))
        else:
            # ensure there is at least one projection between SELECT and FROM
            if from_idx <= 1:
                errors.append(error(line, "Empty SELECT list", "SELECT must specify columns or * before FROM"))
            # ensure a table/identifier follows FROM
            if from_idx + 1 >= len(tokens):
                errors.append(error(line, "Missing table", "FROM must be followed by a table or subquery"))

    # INSERT checks
    elif stmt == "INSERT":
        into_idx = _find_value_idx(tokens, "INTO")
        if 'VALUES' in keywords:
            values_idx = _find_value_idx(tokens, "VALUES")
        elif 'VALUE' in keywords:
            values_idx = _find_value_idx(tokens, "VALUE")
            
        if into_idx == -1 or values_idx == -1:
            errors.append(error(line, "Invalid INSERT", "INSERT must use INTO and VALUES"))
        else:
            if into_idx > values_idx:
                errors.append(error(line, "Invalid INSERT order", "INTO must come before VALUES"))
            if into_idx + 1 >= len(tokens):
                errors.append(error(line, "Missing table", "INTO must be followed by a table name"))

    # UPDATE checks
    elif stmt == "UPDATE":
        set_idx = _find_value_idx(tokens, "SET")
        if set_idx == -1:
            errors.append(error(line, "Missing SET clause", "UPDATE must contain SET"))
        else:
            if set_idx <= 1:
                errors.append(error(line, "Missing table", "UPDATE must specify a table before SET"))

    # DELETE checks
    elif stmt == "DELETE":
        from_idx = _find_value_idx(tokens, "FROM")
        if from_idx == -1:
            errors.append(error(line, "Missing FROM clause", "DELETE must use FROM"))
        else:
            if from_idx + 1 >= len(tokens):
                errors.append(error(line, "Missing table", "FROM must be followed by a table name"))

    # DDL checks (CREATE/DROP/ALTER)
    elif stmt in ("CREATE", "DROP", "ALTER"):
        table_idx = _find_value_idx(tokens, "TABLE")
        if table_idx == -1:
            errors.append(error(line, "Invalid DDL", "DDL must specify TABLE"))
        else:
            if table_idx + 1 >= len(tokens):
                errors.append(error(line, "Missing table name", "TABLE must be followed by an identifier"))

    else:
        errors.append(error(line, "Unsupported SQL", "Only common DML and DDL statements are supported"))

    return errors
