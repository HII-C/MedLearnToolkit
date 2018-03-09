import os
import MySQLdb as sql
from getpass import getpass
from collections import defaultdict

class SemRepDerivedCreation:
    def __init__(self, limit=10000):
        self.semmed_conn = None
        self.semmed_cur = None
        self.semmed_table_name = None

        self.useful_conn = None
        self.useful_cur = None
        self.useful_table_name = None

        self.der_conn = None
        self.der_cur = sql.cursors.Cursor
        self.der_table_name = None
        self.new_der_table = False

        self.limit = limit
        self.list_of_rel_preds = list()
        self.dict_of_pred_occ = defaultdict(int)

    def connect_useful_db(self, database, table_name):
        self.useful_conn = sql.connect(**database)
        self.useful_cur = self.useful_conn.cursor()
        self.useful_table_name = table_name

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
                (PREDICATE VARCHAR(50),
                 SUBJECT_CUI CHAR(8), 
                 SUBJECT_NAME VARCHAR(200),
                 SUBJECT_SEMTYPE CHAR(4),
                 OBJECT_CUI CHAR(8),
                 OBJECT_NAME VARCHAR(200),
                 OBJECT_SEMTYPE CHAR(4),
                 OCC_COUNT INT)""")
            self.new_der_table = True

    def get_n_random_useful_articles(self, n=10000):
        exec_str = f"SELECT * from {self.useful_table_name} ORDER BY RAND() limit {n}"
        self.useful_cur.execute(exec_str)
        return tuple(self.useful_cur)

    def useful_preds_by_PMID(self, pmid_list, n=10000):
        sel_str = "PREDICATE, SUBJECT_CUI, SUBJECT_NAME, SUBJECT_SEMTYPE, OBJECT_CUI, OBJECT_NAME, OBJECT_SEMTYPE"
        exec_str = f"SELECT ({sel_str}) from {self.semmed_table_name} where PMID in {pmid_list} limit {n}"
        self.semmed_cur.execute(exec_str)
        # self.list_of_rel_preds = [*self.list_of_rel_preds, *self.semmed_cur]
        self.list_of_rel_preds = self.semmed_cur

    def assign_occ_to_preds(self):
        for pred in self.list_of_rel_preds:
            pred = tuple(pred)
            self.dict_of_pred_occ[pred] += 1
        
        exec_str = f"INSERT INTO {self.der_table_name} VALUES(%s,%s,%s,%s,%s,%s,%s)"
        val_list = list()
        for val in self.dict_of_pred_occ.items():
            val_list.append(tuple([*val_list[0], val_list[1]]))
        self.der_cur.executemany(exec_str, val_list)
        self.der_conn.commit()

if __name__ == "__main__":
    example = SemRepDerivedCreation()
    user = input("What is the name of the DB user? (Must have access to semmed and derived)\n")
    pw = getpass(f"What is the password for {user}?\n")

    semmed_db = {"user": user, "db": "semmed", 'host': 'db01.healthcreek.org', 'password': pw}
    der_db = {"user": user, "db": "derived", 'host': 'db01.healthcreek.org', 'password': pw}

    der_table_name = input(f"What is the table to be used on {der_db['db']}?\n")
    example.connect_der(der_db, der_table_name)
    print(f'Connected to database: {der_db["db"]} on table: {der_table_name}')

    semmed_table_name = input(f"What is the table to be used on {semmed_db['db']}?\n")
    example.connect_semmed(semmed_db, semmed_table_name)
    print(f'Connected to database: {semmed_db["db"]} on table: {semmed_table_name}')

    ret_pmid_list = example.get_n_random_useful_articles()
    example.useful_preds_by_PMID(ret_pmid_list)
    example.assign_occ_to_preds()