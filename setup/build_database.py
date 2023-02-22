import json
from bs4 import BeautifulSoup
import pandas as pd
from tqdm.auto import tqdm
import sqlite3
import os

os.system('rm -rf stackexchange; mkdir -p stackexchange')

# get database schema
database = json.load(open('database/schema.json'))

conn = sqlite3.connect('stackexchange/stackexchange.db')
cursor = conn.cursor()
schema = database['schemas'][0]
# create tables
for table in schema['tables']:
    cols = [i for i in table['columns'] if i['name'] != 'id']
    columns = ', '.join([f"{col['name']} {col['type']}" for col in cols])
    cmd = f"CREATE TABLE {table['name']} ({columns});"
    print(cmd)
    cursor.execute(cmd)
    
cursor.close()
conn.commit()

dfs = dict()

for table in tqdm(schema['tables']):
    # create dataframe
    df = dict()
    for col in table['columns']:
        df[col['name']] = []
    
    soup = BeautifulSoup(open(f'database/{table["name"]}.xml'), 'lxml')
    
    rows = soup.find_all('row')
    # load data into dataframe
    for row in rows:
        for col in df.keys():
            if col in row.attrs:
                df[col].append(row.attrs[col])
            else:
                df[col].append(None)
    
    df = pd.DataFrame(df)
    for column in table['columns']:
        n = column['name']
        if column['type'] == 'datetime':
            df[n] = pd.to_datetime(df[n])
        elif column['type'] == 'int':
            df[n] = [int(i) if i is not None else None for i in df[n]]
        elif column['type'] == 'boolean':
            newcols = []
            for i in df[n]:
                if i == 'True':
                    newcols.append(True)
                elif i == 'False':
                    newcols.append(False)
                elif i is None:
                    newcols.append(None)
                else:
                    print(i)
                    raise Exception('Not a boolean?')
            df[n] = newcols
        else:
            # keep as object
            continue
        
    for column in df.columns:
        if any(type(i) == list for i in df[column]):
            df[column] = df[column].apply(lambda x: x[0])
        
    # set index of df to id
    df.set_index('id', inplace=True, drop=True)
    
    # make all caps
    df.columns = [i.upper() for i in df.columns]
            
    dfs[table['name']] = df
    
for table_name, df in dfs.items():
    print(table_name)
    df.to_sql(table_name, conn, if_exists='replace')
    
conn.commit()
conn.close()
