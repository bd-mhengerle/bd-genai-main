import os

import pandas as pd
import snowflake.connector

class SFConnection:

    def __init__(
            self,
            user: str,
            password: str,
            account: str,
            warehouse: str
    ):
        self.user = user
        self.password = password
        self.account = account
        self.warehouse = warehouse


    def query(self, query: str) -> pd.DataFrame:
        con = snowflake.connector.connect(
            user=self.user,
            password=self.password,
            account=self.account,
            warehouse=self.warehouse
        )
        with con.cursor() as cur:
            cur.execute(query)
            df = pd.DataFrame(
                cur.fetchall(),
                columns=[col[0] for col in cur.description]
            )
        con.close()
        return df
    
    @classmethod
    def from_env(self):
        return SFConnection(
            user=os.environ['SF_USER'],
            password=os.environ['SF_PASSWORD'],
            account=os.environ['SF_ACCOUNT'],
            warehouse=os.environ['SF_WAREHOUSE']
        )
    
