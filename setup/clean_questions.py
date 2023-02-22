import json
from tqdm.auto import tqdm
from typing import Iterable
import pandas as pd
import sqlglot
import os

table_names = ['badges', 
               'comments', 
               'posthistory', 
               'postlinks', 
               'posts', 
               'tags', 
               'users', 
               'votes']

dialects = [
    'tsql',
    'mysql',
    'postgres',
    'snowflake',
    'sqlite',
    'teradata'
    ]

os.system('rm -rf questions; mkdir -p questions')

def transpile(query):
    transpiled_sql = None
    for dialect in dialects:
        try:
            transpiled_sql = sqlglot.transpile(query, read=dialect, write='sqlite')[0]
        except Exception:
            continue
        
        if transpiled_sql:
            return transpiled_sql
    
    raise Exception('asdf')

            

def clean(questions: Iterable):
    cleaned_queries = []
    irrelevant_queries = []
    unsupported_queries = []
    
    for d in tqdm(questions):
        try:
            # attempt to parse
            parse = sqlglot.parse_one(d['QueryBody'], read='tsql')
            tables = [i.name for i in parse.find_all(sqlglot.exp.Table)]
            # make sure that all tables in query exist
            if all(t.lower() in table_names for t in tables):
                # transpile to sqlite
                d['QueryBody_Original'] = d['QueryBody']
                transpiled_query = transpile(d['QueryBody'])
                d['QueryBody'] = sqlglot.parse_one(transpiled_query, read='sqlite').sql()
                
                # append to clean queries
                cleaned_queries.append(d)
            else:
                irrelevant_queries.append(d)
        except Exception:
            unsupported_queries.append(d)
            
    print(f'Cleaned queries: {len(cleaned_queries)}')
    print(f'Irrelevant queries: {len(irrelevant_queries)}')
    print(f'Unsupported queries: {len(unsupported_queries)}')
    
    return cleaned_queries, irrelevant_queries, unsupported_queries

# clean each set + save as json in questions folder
for split in ['test', 'train', 'val']:
    print(split.upper())
    file_name = f"sede/data/sede/{split}.jsonl"
    data, irrelevant_queries, unsupported_queries = clean(
        json.loads(line) for line in open(file_name)
        )
    
    pd.DataFrame(data).to_json(
        f'questions/{split}.json',
        orient='records'
        )
    
    pd.DataFrame(unsupported_queries).to_json(
        f'questions/unsupported_queries_{split}.json',
        orient='records'
        )
