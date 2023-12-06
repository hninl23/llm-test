import pandas as pd 
from sqlalchemy import create_engine

cnx = create_engine('sqlite:///chroma-collections.parquet.db').connect()
 
# table named 'contacts' will be returned as a dataframe.
df = pd.read_sql_table('collections', cnx)
print(df)