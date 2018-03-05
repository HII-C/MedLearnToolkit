import os
import MySQLdb as sql

class SemRepDerivedCreation:
    def __init__(self, limit=10000):
        self.semmed_conn = None
        self.semmed_cur = None
        self.semmed_table_name = None
        self.der_conn = None
        self.der_cur = None
        self.der_table_name = None
        self.table_name = None
        self.limit = limit

    def connect_semmed(self, database, table_name):
        self.semmed_conn = sql.connect(**database)
        self.semmed_cur = self.semmed_conn.cursor()
        self.semmed_table_name = table_name

    def connect_der(self, database, table_name, drop=False):
        self.der_conn = sql.connect(**database)
        self.der_cur = self.der_conn.cursor()
        self.der_table_name = table_name
        if drop:
            print(f"Are you sure you want to drop the table \"{table_name}\"?")
            print("ALL DATA WILL BE LOST, THIS IS NOT REVERSABLE")
            user_resp = input("y/n?")
            if user_resp != "y":
                print("Exiting now")
                exit()
            else:
                print("Okay, data being dropped")
            self.der_cur.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.der_cur.execute(f"""CREATE TABLE {table_name} 
                (SUBJECT_CUI CHAR(8), 
                 SUBJECT_NAME VARCHAR(200),
                 SUBJECT_SEMTYPE CHAR(4),
                 OBJECT_CUI CHAR(8),
                 OBJECT_NAME VARCHAR(200),
                 OBJECT_SEMTYPE CHAR(4),
                 OCC_COUNT INT)""")

    def get_n_random_valid_articles(self, n=10000):
        exec_str = f"SELECT * from {self.semmed_table_name} "

    def relevant_semmed_entries(self, pmid_list):
        exec_str = (f"SELECT * from {self.table_name} where PMID in {tuple(pmid_list)} limit {self.limit}")
        