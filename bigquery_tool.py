# bigquery_tool.py
from google.cloud import bigquery
import pandas as pd

class BigQueryTool:
    def __init__(self, client):
        self.client = client

    def query(self, sql_query):
        query_job = self.client.query(sql_query)
        result = query_job.result()
        data = [dict(row) for row in result]
        return pd.DataFrame(data)
