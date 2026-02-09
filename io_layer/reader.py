import os
def read_single_file(file_path):
    queries=[]
    with open (file_path,'r') as f:
        content=f.read().strip()
        # Split by semicolon to handle multiple queries in one file
        # This is more robust than line-based splitting
        raw_queries = [q.strip() for q in content.split(';') if q.strip()]
        
        if not raw_queries:
            return queries
            
        for query in raw_queries:
            queries.append({"source":os.path.basename(file_path),"sql": query})
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
