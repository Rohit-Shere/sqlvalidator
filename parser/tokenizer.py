import re

TOKENS = [
    # Extended keywords for complex queries
    ("KEYWORD", r"\b(SELECT|FROM|WHERE|INSERT|INTO|VALUE|VALUES|UPDATE|SET|DELETE|CREATE|DROP|ALTER|TABLE|IN|LIMIT|JOIN|INNER|LEFT|RIGHT|FULL|OUTER|CROSS|ON|AND|OR|NOT|DISTINCT|AS|GROUP|BY|HAVING|ORDER|ASC|DESC|OFFSET|UNION|INTERSECT|EXCEPT|CASE|WHEN|THEN|ELSE|END|BETWEEN|LIKE|EXISTS|WITH|OFFSET|RECURSIVE|ALL|ANY|SOME|CAST|INTERVAL|EXTRACT|OVER|PARTITION|ROW|ROWS|PRECEDING|FOLLOWING|CURRENT|UNBOUNDED|RANGE|EXCLUDE|NULLS|FIRST|LAST|PRIMARY|FOREIGN|KEY|REFERENCES|CONSTRAINT|INDEX|UNIQUE|CHECK|DEFAULT|AUTO_INCREMENT|COLLATE|COMMENT|ENGINE|CHARACTER|CHARSET|UNSIGNED|SIGNED|ZEROFILL|BINARY|PRECISION|SCALE|DATE|TIME|TIMESTAMP|DATETIME|YEAR|MONTH|DAY|HOUR|MINUTE|SECOND|MICROSECOND|INTERVAL|WEEK|QUARTER|CENTURY|DECADE|AGE|EPOCH|TIMEZONE|AT|ZONE)\b"),
    ("AGGREGATE", r"\b(COUNT|SUM|AVG|MIN|MAX|STRING_AGG|ARRAY_AGG|STDDEV|VARIANCE|MEDIAN|MODE|PERCENTILE|LISTAGG)\b"),
    ("STAR", r"\*"),
    ("IDENTIFIER", r"[a-zA-Z_][a-zA-Z0-9_]*"),
    ("NUMBER", r"\b\d+(?:\.\d+)?\b"),  # Added float support
    ("STRING", r"'(?:[^'\\]|\\.)*'"),  # Handles escaped quotes like 'don\'t' 
    ("OPERATOR", r"(=|<>|!=|<|>|<=|>=|\|\||&&|\+|-|\*|/|%)"),
    ("SYMBOL", r"[(),;.]"),
    ("WHITESPACE", r"\s+"),
]

def tokenize(query):
    """
    Tokenizes SQL query into (type, value, line) tuples.
    Tracks line numbers for better error reporting.
    """
    tokens = []
    i = 0
    line = 1
    
    while i < len(query):
        matched = False

        for ttype, pattern in TOKENS:
            m = re.match(pattern, query[i:], re.IGNORECASE)
            if m:
                val = m.group(0)
                if ttype != "WHITESPACE":
                    tokens.append((ttype, val.upper(), line))
                
                # Track newlines for line counting
                line += val.count('\n')
                i += len(val)
                matched = True
                break

        if not matched:
            raise SyntaxError(f"Invalid character near '{query[i]}' at line {line}")

    return tokens