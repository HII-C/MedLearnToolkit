from getpass import getpass
import MySQLdb as sql

class MimicToUmlsCui:
    def __init__(self):
        self.gen_conn = None
        self.gen_cur = None
        self.mimic_conn = None
        self.mimic_cur = None
        self.umls_conn = None
        self.umls_cur = None
        self.umls_table = None
        self.der_conn = None
        self.der_cur = None

    def connect_gen_db(self, database):
        self.gen_conn = sql.connect(**database)
        self.gen_cur = self.gen_conn.cursor()

    def connect_mimic_db(self, database):
        self.mimic_conn = sql.connect(**database)
        self.mimic_cur = self.mimic_conn.cursor()

    def connect_umls_db(self, database):
        self.umls_conn = sql.connect(**database)
        self.umls_cur = self.umls_conn.cursor()
        self.umls_table = "MRCONSO"

    def connect_der_db(self, database):
        self.der_conn = sql.connect(**database)
        self.der_cur = self.der_conn.cursor()

    def table_map_itemid_cui(self, table, source, drop=False, n=10000):
        if drop is True:
            self.mimic_cur.execute(f"DROP TABLE IF EXISTS {table}")
            create_str_dict = {
                        "D_LABITEMS": """(CUI CHAR(8), AUI VARCHAR(9), SAB VARCHAR(40), CODE CHAR(100),
                                    ITEMID SMALLINT UNSIGNED, LOINC_CODE VARCHAR(255), LABEL VARCHAR(100))""",
                        "D_ICD_DIAGNOSES": """(CUI CHAR(8), SAB VARCHAR(40), CODE CHAR(100),
                                        ICD9_CODE VARCHAR(10), SHORT_TITLE VARCHAR(50)"""
            }
            self.mimic_cur.execute(f"CREATE TABLE {table} {create_str_dict[source]}")

        on_str_dict = {
            "D_LABITEMS": """
                            u.LAT = 'ENG' and
                            u.SAB = 'LNC' and 
                            u.CODE = m.LOINC_CODE
                          """,
            "D_ICD_DIAGNOSES": """
                            u.SAB = 'ICD9CM' and
                            u.LAT = 'ENG' and
                            u.CODE = CONCAT(LEFT(m.ICD9_CODE, 3), '.', RIGHT(m.ICD9_CODE, 2))
                               """
        }
        sel_str_dict = {
            "D_LABITEMS": "u.CUI, u.AUI, u.SAB, u.CODE, m.ITEMID, m.LOINC_CODE, m.LABEL",
            "D_ICD_DIAGNOSES": "u.CUI, u.SAB, u.CODE, m.ICD9_CODE, m.SHORT_TITLE"
        }
        sel_str = f"SELECT DISTINCT {sel_str_dict[source]}"
        j_str = f"""umls.MRCONSO as u INNER JOIN mimic.{source} as m ON {on_str_dict[source]}"""
        limit_str = f" LIMIT {n}"
        if n is None:
            limit_str = ""
        exec_str = f"INSERT INTO derived.{table} SELECT {sel_str_dict[source]} from {j_str}{limit_str}" #temp
        self.der_cur.execute(exec_str)
        self.der_conn.commit()
    
    def mimic_table_to_umls_cui(self, source, umls_map, table, drop=False, n=1000):
        source_to_int = {"DIAGNOSES_ICD": 0, "LABEVENTS": 1}
        if drop == True:
            self.der_cur.execute(f"DROP TABLE IF EXISTS {table}")
            tbl_attr = "(SUBJECT_ID INT, HADM_ID INT, CUI CHAR(8), SOURCE SMALLINT UNSIGNED)"
            self.der_cur.execute(f"CREATE TABLE derived.{table} {tbl_attr}")
        j_str = f"""mimic.{source} AS m INNER JOIN derived.{umls_map} AS d ON d.ITEMID = m.ITEMID"""
        
        select_str = f"m.SUBJECT_ID, m.HADM_ID, d.CUI, {source_to_int[source]}"
        limit_str = f" LIMIT {n}"
        if n is None:
            limit_str = ""
        self.der_cur.execute(f"""INSERT INTO derived.{table} SELECT {select_str} from {j_str}{limit_str}""")
        self.der_conn.commit()

if __name__ == "__main__":
    print("Starting")
    # user = input("What is the user to access the databases?\n")
    user = 'root'
    # user = 'hiic' #temp measure for access
    pw = getpass(f'What is the password for the user {user}?\n')

    gen_db = {'user': user, 'host': 'db01.healthcreek.org', 'password': pw}
    mimic_db = {'user': user, 'db': 'mimic', 'host': 'db01.healthcreek.org', 'password': pw}
    umls_db = {'user': user, 'db': 'umls', 'host': 'db01.healthcreek.org', 'password': pw}
    der_db = {'user': user, 'db': 'derived', 'host': 'db01.healthcreek.org', 'password': pw}

    example = MimicToUmlsCui()
    example.connect_gen_db(gen_db)
    example.connect_mimic_db(mimic_db)
    example.connect_umls_db(umls_db)
    example.connect_der_db(der_db)
    example.table_map_itemid_cui('ICD9_to_CUI', "D_ICD9_DIAGNOSES", drop=True)
    # example.mimic_table_to_umls_cui("LABEVENTS",
    #                                 "ItemIdToCUI", 
    #                                 "patients_as_cui", 
    #                                 drop=True,
    #                                 n=None)
