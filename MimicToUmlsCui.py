import MySQLdb as sql
from getpass import getpass

class MimicToUmlsCui:
    def __init__(self):
        self.gen_conn = None
        self.gen_cur = None
        self.mimic_conn = None
        self.mimic_cur = None
        self.umls_conn = None
        self.umls_cur = None
        self.umls_table = None

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

    def create_derived(self, tbl, n=10000):
        self.mimic_cur.execute(f"DROP TABLE IF EXISTS {tbl}")
        create_str = """(CUI CHAR(8), AUI VARCHAR(9), SAB VARCHAR(40), CODE CHAR(100), ITEMID SMALLINT UNSIGNED, LOINC_CODE VARCHAR(255))"""
        self.mimic_cur.execute(f"CREATE TABLE {tbl}{create_str}")
        # from_str = " umls.MRCONSO, mimic.D_LABITEMS"
        # where_str = """  umls.MRCONSO t1 umls.MRCONSO.CODE = mimic.D_LABITEMS.LOINC_CODE 
        # and umls.MRCONSO.LAT = 'ENG' and umls.MRCONSO.TTY = 'CN' and umsl.MRCONSO.SAB = 'LNC'"""
        j_str = """
        umls.MRCONSO t1 
            INNER JOIN
        mimic.D_LABITEMS t2 
            ON 
        t1.STR = t2.LABEL and
        t1.LAT = 'ENG' and
        t1.TTY = 'CN' and
        t1.SAB = 'LNC'
        """
        sel_str = "SELECT CUI, AUI, SAB, CODE, ITEMID, LOINC_CODE"
        exec_str = f"INSERT INTO {tbl} {sel_str} from {j_str} limit {n}"
        self.mimic_cur.execute(exec_str)
        self.mimic_conn.commit()

if __name__ == "__main__":
    print("Starting")
    # user = input("What is the user to access the databases?\n")
    user = 'root'
    pw = getpass(f'What is the password for the user {user}?\n')

    gen_db = {'user': user, 'host': 'db01.healthcreek.org', 'password': pw}
    mimic_db = {'user': user, 'db': 'mimic', 'host': 'db01.healthcreek.org', 'password': pw}
    umls_db = {'user': user, 'db': 'umls', 'host': 'db01.healthcreek.org', 'password': pw}

    example = MimicToUmlsCui()
    example.connect_gen_db(gen_db)
    example.connect_mimic_db(mimic_db)
    example.connect_umls_db(umls_db)
    example.create_derived('ItemIdToCUI')
