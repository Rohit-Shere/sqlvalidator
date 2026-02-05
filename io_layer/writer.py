import json
import os

def write_jsonf(q_id,src,sql,status,errors):
    os.makedirs("outputs",exist_ok=True)

    data={"q_id":q_id,"source":src,"sql":sql,"status":status,"errors":errors}

    with open(f"outputs/query_{q_id}.json",'w') as f:
        json.dump(data,f,indent=4)
