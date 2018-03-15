import os
import pandas as pd
import MySQLdb as sql
from getpass import getpass

class PatientMatrixGenForML:

    def __init__(self):
        self.patient_conn = None
        self.patient_cur = None
        self.patient_table_name_one = None
        self.patient_table_name_two = None
        self.patient_data_one = None
        self.patient_data_two = None
        self.relevant_pred_conn = None
        self.relevant_pred_cur = None
        self.relevant_pred_table_name = None

    def connect_patient_db(self, database, table_name_one, table_name_two):
        self.patient_conn = sql.connect(**database)
        self.patient_cur = self.patient_conn.cursor()
        self.patient_table_name_one = table_name_one
        self.patient_table_name_two = table_name_two

    def connect_relevant_pred_db(self, database, table_name):
        self.relevant_pred_conn = sql.connect(**database)
        self.relevant_pred_cur = self.relevant_pred_conn.cursor()
        self.relevant_pred_table_name = table_name

    def get_patient_records(self, select_str_one, select_str_two, n=10000):
        exec_str_one = f"SELECT {select_str_one} from {self.patient_table_name_one} LIMIT {n}"
        self.patient_cur.execute(exec_str_one)
        self.patient_data_one = self.patient_cur.fetchall()

        split_list = select_str_one.split(', ')
        idx_val = None
        try:
            try:
                idx_val = split_list.index('HADM_ID')
            except:
                idx_val = split_list.index('SUBJECT_ID')
        except:
            print("Need to keep track of at least one of \'SUBJECT_ID\' or \'HADM_ID\'\n")
            print("Add one of these to your \'select_str_one\'\n")
            exit()

        find_val = split_list[idx_val]
        tuple_of_id = tuple([x[idx_val] for x in self.patient_data_one])

        exec_str_two = f"""SELECT {select_str_two} from {self.patient_table_name_two}
                        WHERE {find_val} in {tuple_of_id} limit {n}"""

        self.patient_cur.execute(exec_str_two)
        self.patient_data_two = self.patient_cur.fetchall()
    
    def find_n_relevant_rel(self, select_str, where_str=None, n=10000):
        exec_str = f"""SELECT {select_str} from {self.relevant_pred_table_name}
                    {where_str} ORDER BY OCC_COUNT DESC limit {n}"""
        self.relevant_pred_cur.execute(exec_str)
        
if __name__ == "__main__":
    example = PatientMatrixGenForML()
    # user = input("What is the user to access the databases?\n")
    user = 'greenes2018'
    pw = getpass(f'What is the password for the user {user}?\n')
    patient_db = {'user': user, 'db': 'mimic', 'host': 'db01.healthcreek.org', 'password': pw}
    relev_pred_db = {'user': user, 'db': 'derived', 'host': 'db01.healthcreek.org', 'password': pw}

    example.connect_patient_db(patient_db, 'LABEVENTS', 'DIAGNOSES_ICD')
    example.connect_relevant_pred_db(relev_pred_db, "austin_pred_occ_test")

    str_one = 'SUBJECT_ID, ITEMID'
    str_two = 'SUBJECT_ID, ICD9_CODE'
    # example.