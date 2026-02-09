"""
parser package

THIS PACKAGE CONTAINS:
-- tokenizer for lexical analysis
--grammar parser for sql statement
--syntax and structural rules

"""

from .tokenizer import tokenize
from .parser import parse
from .rules import apply_rules


