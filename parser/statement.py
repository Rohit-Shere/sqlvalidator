def get_statement_type(tokens):
    """Extract the first keyword as the statement type."""
    if not tokens:
        return None
    # tokens now have 3 elements: (type, value, line)
    # Extract just the value (index 1)
    return tokens[0][1]
