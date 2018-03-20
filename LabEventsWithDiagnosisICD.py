import MySQLdb as sql
from getpass import getpass

class LabEventsWithDiagnosesICD:
    def __init__(self):
        self.gen_conn = None
        self.gen_cur = None
        self.mimic_conn = None
        self.mimic_cur = None
        self.umls_conn = None
        self.umls_cur = None
        self.umls_table = None

    def connect_mimic_db(self, database):
        self.mimic_conn = sql.connect(**database)
        self.mimic_cur = self.mimic_conn.cursor()

    def create_derived(self, tbl, n=10000):
        lab_events_str = """mimic.LABEVENTS"""
        diag_icd_str = """mimic.DIAGNOSES_ICD"""

        create_str = """(SUBJECT_ID SMALLINT UNSIGNED, HADM_ID SMALLINT UNSIGNED, ITEM_ID UNSIGNED INT, ICD9_CODE UNSIGNED INT, SOURCE SMALLINT UNSIGNED)"""
        select_str = """SELECT SUBJECT_ID, HADM_ID, ITEM_ID"""
            
        exec_str = f"""CREATE TABLE {tbl}{create_str} AS {select_str} FROM {lab_events_str}""" #creates the new table from lab_events
        update_str = f"""UPDATE {tbl} SET SOURCE = 0""" #0 means row was from mimic.LABEVENTS, 1 means row was from DIAGNOSES_ICD

        self.mimic_cur.execute(exec_str)
        self.mimic_conn.commit()
        self.mimic_cur.execute(update_str)
        self.mimic_conn.commit()

        #add DIAGNOSES_ICD columns to derived layer
        insert_str = f"""INSERT INTO {tbl} (SUBJECT_ID, HADM_ID, ICD9_CODE) SELECT SUBJECT_ID, HADM_ID, ICD9_CODE FROM {diag_icd_str}"""
        update_str = f"""UPDATE {tbl} SET SOURCE = 1 WHERE ICD9_CODE IS NOT NULL""" #change the flag to show row came from DIAGNOSES_ICD

        self.mimic_cur.execute(insert_str)
        self.mimic_conn.commit()
        self.mimic_cur.execute(update_str)
        self.mimic_conn.commit()


if __name__ == "__main__":
    print("Starting")
    user = 'root'
    pw = getpass(f'What is the password for the user {user}?\n')

    mimic_db = {'user': user, 'db': 'mimic', 'host': 'db01.healthcreek.org', 'password': pw}

    example = LabEventsWithDiagnosisICD()
    example.connect_mimic_db(mimic_db)
    example.create_derived('LabEventsWithDiagnosesICD')
