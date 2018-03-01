import os
import MySQLdb as sql

class SemRep:
    def __init__(self):
        self.cursor = None
        self.connection = None
        self.query_val = None
        self.table = None
        self.limit = 10000
    
    def connect_db(self, database):
        host_ = database["host"]
        user_ = database["user"]
        password_ = database["password"]
        self.connection = sql.connect(host=host_, user=user_, password=password_)
        self.cursor = self.connection.cursor()

    def gen_pmid_from_art_type(self, )

    def minimize_table_by_art_type(self, connection, cursor, pmid_list):
        exec_str = (f"SELECT * from {self.table} where PMID in {tuple(pmid_list)} limit {self.limit}")