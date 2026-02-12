from parser.errors import error
from parser.statement import get_statement_type


def _find_value_idx(tokens, value):
    """Find index of token with given value."""
    for i, token in enumerate(tokens):
        if token[1] == value:
            return i
    return -1


def _find_all_indices(tokens, value):
    """Find all indices of tokens with given value."""
    return [i for i, token in enumerate(tokens) if token[1] == value]


# =========================
# SELECT VALIDATION
# =========================
def _validate_select(tokens, sql=""):
    errors = []
    line = 1

    from_idx = _find_value_idx(tokens, "FROM")

    if from_idx == -1:
        errors.append(error(line, "Missing FROM clause",
                            "SELECT must contain FROM"))
    else:
        # Ensure SELECT list is not empty
        if from_idx <= 1:
            errors.append(error(
                line,
                "Empty SELECT list",
                "SELECT must specify columns or * before FROM"
            ))

        # Ensure table exists after FROM
        if from_idx + 1 >= len(tokens):
            errors.append(error(
                line,
                "Missing table",
                "FROM must be followed by a table or subquery"
            ))

    # WHERE validation
    where_idx = _find_value_idx(tokens, "WHERE")
    if where_idx != -1 and where_idx + 1 >= len(tokens):
        errors.append(error(
            line,
            "Empty WHERE clause",
            "WHERE must be followed by a condition"
        ))

    # GROUP BY validation
    group_idx = _find_value_idx(tokens, "GROUP")
    if group_idx != -1:
        if group_idx + 1 >= len(tokens) or tokens[group_idx + 1][1] != "BY":
            errors.append(error(
                line,
                "Invalid GROUP BY",
                "GROUP must be followed by BY"
            ))
        elif group_idx + 2 >= len(tokens):
            errors.append(error(
                line,
                "Empty GROUP BY",
                "GROUP BY must specify columns"
            ))

    # HAVING validation
    having_idx = _find_value_idx(tokens, "HAVING")
    if having_idx != -1:
        if group_idx == -1:
            errors.append(error(
                line,
                "Invalid HAVING",
                "HAVING requires GROUP BY"
            ))
        elif having_idx + 1 >= len(tokens):
            errors.append(error(
                line,
                "Empty HAVING clause",
                "HAVING must be followed by a condition"
            ))

    # ORDER BY validation
    order_idx = _find_value_idx(tokens, "ORDER")
    if order_idx != -1:
        if order_idx + 1 >= len(tokens) or tokens[order_idx + 1][1] != "BY":
            errors.append(error(
                line,
                "Invalid ORDER BY",
                "ORDER must be followed by BY"
            ))
        elif order_idx + 2 >= len(tokens):
            errors.append(error(
                line,
                "Empty ORDER BY",
                "ORDER BY must specify columns"
            ))

    # LIMIT validation
    limit_idx = _find_value_idx(tokens, "LIMIT")
    if limit_idx != -1 and limit_idx + 1 >= len(tokens):
        errors.append(error(
            line,
            "Empty LIMIT clause",
            "LIMIT must be followed by a number"
        ))

    return errors


# =========================
# INSERT VALIDATION
# =========================
def _validate_insert(tokens):
    errors = []
    line = 1

    into_idx = _find_value_idx(tokens, "INTO")
    values_idx = _find_value_idx(tokens, "VALUES")

    if into_idx == -1 or values_idx == -1:
        errors.append(error(
            line,
            "Invalid INSERT",
            "INSERT must use INTO and VALUES"
        ))
    else:
        if into_idx > values_idx:
            errors.append(error(
                line,
                "Invalid INSERT order",
                "INTO must come before VALUES"
            ))

        if into_idx + 1 >= len(tokens):
            errors.append(error(
                line,
                "Missing table",
                "INTO must be followed by a table name"
            ))

        if values_idx + 1 >= len(tokens) or tokens[values_idx + 1][1] != "(":
            errors.append(error(
                line,
                "Invalid VALUES",
                "VALUES must be followed by (...)"
            ))

    return errors


# =========================
# UPDATE VALIDATION
# =========================
def _validate_update(tokens):
    errors = []
    line = 1

    set_idx = _find_value_idx(tokens, "SET")

    if set_idx == -1:
        errors.append(error(
            line,
            "Missing SET clause",
            "UPDATE must contain SET"
        ))
    else:
        if set_idx <= 1:
            errors.append(error(
                line,
                "Missing table",
                "UPDATE must specify a table before SET"
            ))

        if set_idx + 1 >= len(tokens):
            errors.append(error(
                line,
                "Empty SET clause",
                "SET must be followed by column assignments"
            ))

        where_idx = _find_value_idx(tokens, "WHERE")
        if where_idx != -1 and where_idx + 1 >= len(tokens):
            errors.append(error(
                line,
                "Empty WHERE clause",
                "WHERE must be followed by a condition"
            ))

    return errors


# =========================
# DELETE VALIDATION
# =========================
def _validate_delete(tokens):
    errors = []
    line = 1

    from_idx = _find_value_idx(tokens, "FROM")

    if from_idx == -1:
        errors.append(error(
            line,
            "Missing FROM clause",
            "DELETE must use FROM"
        ))
    else:
        if from_idx + 1 >= len(tokens):
            errors.append(error(
                line,
                "Missing table",
                "FROM must be followed by a table name"
            ))

    return errors


# =========================
# DDL VALIDATION
# =========================
def _validate_ddl(tokens):
    errors = []
    line = 1

    table_idx = _find_value_idx(tokens, "TABLE")

    if table_idx == -1:
        errors.append(error(
            line,
            "Invalid DDL",
            "DDL must specify TABLE"
        ))
    else:
        if table_idx + 1 >= len(tokens):
            errors.append(error(
                line,
                "Missing table name",
                "TABLE must be followed by an identifier"
            ))

    return errors


# =========================
# MAIN PARSE FUNCTION
# =========================
def parse(sql, tokens):
    errors = []

    if not tokens:
        return [error(1, "Empty query", "No SQL statement found")]

    stmt = get_statement_type(tokens)

    if not stmt:
        return [error(1, "Empty query", "No SQL statement found")]

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
    else:
        errors.append(error(
            1,
            "Unsupported SQL",
            f"Statement type '{stmt}' is not yet supported"
        ))

    return errors
