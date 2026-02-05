from parser.errors import error
from parser.statement import get_statement_type

def parse(sql,tokens):
  errors=[]
  line=1
  stmt=get_statement_type(tokens)
  keywords=[v for _, v in tokens]
  if stmt == "SELECT":
    if "FROM" not in keywords:
      errors.append(error(line, "Missing FROM clause", "SELECT must contain FROM"))
  
  elif(stmt=="INSERT"):
    if("INTO" not in keywords or "VALUES" not in keywords):
      errors.append(error(line,"Invalid INSERT","INSERT must useINTO and VALUES"))
      
  elif(stmt=="UPDATE"):
    if("SET" not in keywords):
      errors.append(error(line,"Missing SET clause","UPDATE must contain SET"))

  elif(stmt== "DELETE"):
    if("FROM" not in keywords):
      errors.append(error(line,"Missing FROM clause","DELETE must use FROM"))

  elif(stmt in("CREATE","DROP","ALTER")):
    if("TABLE" not in keywords):
      errors.append(error(line,"Invalid DDL","DDL must specify TABLE"))

  else:
    errors.append(error(line,"Unsupported SQL","Only DML and DDL are supported"))

  return errors
  
  
