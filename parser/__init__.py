"""
parser package

THIS PACKAGE CONTAINS:
-- tokenizer for lexical analysis
--grammar parser for sql statement
--syntax and structural rules

"""

from parser.tokenizer import tokenize
from parser.parser import parse
from parser.rules import apply_rules


