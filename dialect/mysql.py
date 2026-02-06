from dialect.base import Dialect
from parser.errors import error

class MySQLDialect(Dialect):
  def allowed_statements(self):
    return ["SELECT","INSERT","UPDATE","DELETE", "CREATE", "DROP", "ALTER"]

  def max_subquery_depth(self):
    return 4

  def forbidden_keywords(self):
    return[]

  def validate_statement(self,stmt,tokens):
    return []

  def validate_clauses(self,stmt,tokens):
    errors=[]
    keyword=[v for _,v in tokens]
    if ("LIMIT" in keyword):
      idx=keyword.index("LIMIT")
      if(idx==len(keyword)-1):
        errors.append(error(1,"Invalid LIMIT","LIMIT must be followed by number"))
    return errors

  def validate_ddl(self,stmt,tokens):
    return[]
