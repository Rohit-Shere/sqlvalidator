import re

TOKENS = [
    ("KEYWORD", r"\b(SELECT|FROM|WHERE|INSERT|INTO|VALUE|VALUES|UPDATE|SET|DELETE|CREATE|DROP|ALTER|TABLE|IN|LIMIT)\b"),
    ("STAR", r"\*"),
    ("IDENTIFIER", r"[a-zA-Z_][a-zA-Z0-9_]*"),
    ("NUMBER", r"\b\d+\b"),
    ("STRING", r"'[^']*'"),
    ("OPERATOR", r"(=|<|>|<=|>=|!=)"),
    ("SYMBOL", r"[(),;]"),
    ("WHITESPACE", r"\s+"),
]

def tokenize(query):
    tokens = []
    i = 0
    while i < len(query):
        matched = False

        for ttype, pattern in TOKENS:
            m = re.match(pattern, query[i:], re.IGNORECASE)
            if m:
                val = m.group(0)
                if ttype != "WHITESPACE":
                    tokens.append((ttype, val.upper()))
                i += len(val)
                matched = True
                break

        if not matched:
            raise SyntaxError(f"Invalid character near '{query[i]}'")

    return tokens
  
