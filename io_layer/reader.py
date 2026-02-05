import os
def read_single_file(file_path):
    queries=[]
    with open (file_path,'r') as f:
        content=f.read().strip()
        #there are mulpiple queries in single file
        lines=[line.strip() for line in content.splitlines() if line.strip()]

        if len(lines)>1:#file containing multiple queries
            for line in lines:
                queries.append({"source":os.path.basename(file_path),"sql": line})
        else:
            queries.append({"source":os.path.basename(file_path),"sql": content})
    return queries


def read_input(path):
    all_queries=[]
    if os.path.isfile(path):
        all_queries.extend(read_single_file(path))
    elif os.path.isdir(path):
        for file in os.listdir(path):
            file_path=os.path.join(path,file)
            if os.path.isfile(file_path):
                all_queries.extend(read_single_file(file_path))
    else:
        raise ValueError(f"Invalid path: {path}")
    return all_queries
