import ibm_db
import pypyodbc
from abc import ABCMeta, abstractmethod


class DBConnector(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, host: str = None, db: str = None, port: int = None, uid: str = None, pwd: str = None): pass

    @abstractmethod
    def exec_query(self, query: str): pass

    @abstractmethod
    def close_conn(self): pass


class DB2Connector(DBConnector):
    def __init__(self, host: str = None, db: str = None, port: int = None, uid: str = None, pwd: str = None):
        self.conn = ibm_db.connect(
            f"DATABASE={db};HOSTNAME={host};PORT={port};UID={uid};PWD={pwd}",
            "",
            ""
        )

    def exec_query(self, query: str) -> tuple:
        statement_obj = ibm_db.exec_immediate(self.conn, query)
        yield ibm_db.fetch_tuple(statement_obj)

    def close_conn(self):
        ibm_db.close(self.conn)


# # DB2 EXAMPLE
# db2Sample = DB2Connector(
#     host='172.17.0.4',
#     db='SAMPLE',
#     port=50000,
#     uid='test',
#     pwd='L0frt12'
# )
# res = db2Sample.exec_query("SELECT CURRENT TIMESTAMP(8) FROM SYSIBM.SYSDUMMY1;")
# db2Sample.close_conn()
# print(res)

class MSSqlConnector(DBConnector):

    def __init__(self, host: str = None, db: str = None, port: int = 1433, uid: str = None, pwd: str = None):
        self.conn = pypyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER=tcp:{host};PORT={port};DATABASE={db};UID={uid};PWD={pwd}')

    def exec_query(self, query: str):
        crs = self.conn.cursor()
        crs.execute(query)
        yield crs.fetchall()

    def close_conn(self):
        self.conn.close()

# # MS SQL EXAMPLE
# msSqlSample = MSSqlConnector(
#     host="172.17.0.2",
#     db="",
#     port=1433,
#     uid="sa",
#     pwd="qwerty12345",
# )
#
# res = msSqlSample.exec_query("select @@version;")
# for x in res:
#     print(x)
