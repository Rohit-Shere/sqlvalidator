from parser.errors import error

def apply_rules(sql,max_depth):
  errors=[]
  line=1
  if(sql.count("(") != sql.count(")")):
    errors.append(error(line ,"Unmatched parentheses", "Number of ( and ) must be equal"))
  if(sql.count("'")%2 !=0):
    errors.append(error(line,"Unclosed string literal ","string must start and end with single quotes"))
  depth=0
  max_seen=0
  for ch in sql:
    if (ch =="("):  
      depth+=1
      max_seen=max(max_seen,depth)
    elif(ch==")"):
      depth-=1
  if (max_seen>max_depth):
    errors.append(error(line,"Subquery nested too deep",f"Maximum allowed nesting is {max_depth}"))
  return errors
    
