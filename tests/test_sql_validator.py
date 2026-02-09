import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from parser.tokenizer import tokenize
from parser.parser import parse
from parser.rules import apply_rules
from parser.statement import get_statement_type
from dialect.ansi import AnsiDialect
from dialect.mysql import MySQLDialect


def test_tokenizer_valid():
    tokens = tokenize("SELECT name FROM users")
    assert tokens[0][1] == "SELECT"


def test_tokenizer_invalid_char():
    with pytest.raises(SyntaxError):
        tokenize("SELECT * FROM users #")


def test_statement_type():
    tokens = tokenize("SELECT * FROM users")
    assert get_statement_type(tokens) == "SELECT"


def test_unmatched_parentheses():
    errors = apply_rules("SELECT * FROM users WHERE id = (1", 2)
    assert errors


def test_unclosed_string():
    errors = apply_rules("SELECT * FROM users WHERE name='John", 2)
    assert errors


def test_select_missing_from():
    sql = "SELECT name"
    errors = parse(sql, tokenize(sql))
    assert errors


def test_valid_select():
    sql = "SELECT name FROM users"
    assert parse(sql, tokenize(sql)) == []


def test_empty_where():
    sql = "SELECT * FROM users WHERE"
    assert parse(sql, tokenize(sql))


def test_valid_insert():
    sql = "INSERT INTO users VALUES (1,'John')"
    assert parse(sql, tokenize(sql)) == []


def test_invalid_insert():
    sql = "INSERT INTO users (id,name)"
    assert parse(sql, tokenize(sql))


def test_update_missing_set():
    sql = "UPDATE users name='John'"
    assert parse(sql, tokenize(sql))


def test_valid_update():
    sql = "UPDATE users SET name='John' WHERE id=1"
    assert parse(sql, tokenize(sql)) == []


def test_delete_missing_from():
    sql = "DELETE users WHERE id=1"
    assert parse(sql, tokenize(sql))


def test_valid_delete():
    sql = "DELETE FROM users WHERE id=1"
    assert parse(sql, tokenize(sql)) == []


def test_join_without_on():
    sql = "SELECT * FROM users INNER JOIN orders"
    assert parse(sql, tokenize(sql))


def test_valid_join():
    sql = "SELECT * FROM users INNER JOIN orders ON users.id=orders.uid"
    assert parse(sql, tokenize(sql)) == []


def test_subquery():
    sql = "SELECT * FROM users WHERE id IN (SELECT uid FROM orders)"
    assert parse(sql, tokenize(sql)) == []


def test_ansi_limit_not_allowed():
    sql = "SELECT * FROM users LIMIT 5"
    d = AnsiDialect()
    errors = []
    errors += apply_rules(sql, d.max_subquery_depth())
    errors += parse(sql, tokenize(sql))
    errors += d.validate_clauses("SELECT", tokenize(sql))
    assert errors


def test_mysql_limit_allowed():
    sql = "SELECT * FROM users LIMIT 5"
    d = MySQLDialect()
    errors = []
    errors += apply_rules(sql, d.max_subquery_depth())
    errors += parse(sql, tokenize(sql))
    errors += d.validate_clauses("SELECT", tokenize(sql))
    assert errors == []
