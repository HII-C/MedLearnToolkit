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
        # create_str = "CUI CHAR(8), AUI VARCHAR(9), SAB VARCHAR(40), CODE CHAR(100), ITEMID SMALLINT UNSIGNED, LOINC_CODE VARCHAR(255))"
        create_str = """(CUI CHAR(8), AUI VARCHAR(9), SAB VARCHAR(40), CODE CHAR(100))"""
        self.mimic_cur.execute(f"CREATE TABLE {tbl}{create_str}") 
        # t1.STR = t2.LABEL and
        #j_str = """
        #umls.MRCONSO t3
        #INNER JOIN mimic.D_LABITEMS t2 ON t3.CODE LIKE t2.LOINC_CODE and t3.SAB = 'LNC'
        #INNER JOIN umls.MRSAT t1 ON t3.LAT = 'ENG' and t3.TTY = 'CN' and t3.CUI = t1.CUI
        #"""
        j_str = ("SELECT conso.CUI, conso.AUI, conso.SAB, conso.CODE FROM "
            "(SELECT * FROM umls.MRSAT as sat JOIN mimic.D_LABITEMS as lab ON "
                "sat.CODE = lab.LOINC_CODE and "
                "sat.SAB = 'LNC' and "
                "sat.SUI IS NOT NULL and "
                "sat.METAUI IS NOT NULL) as temp "
            "JOIN umls.MRCONSO as conso ON "
                "temp.CUI = conso.CUI and "
                "conso.SAB = 'LNC' and "
                "conso.TS = 'P' and "
                "conso.TTY = 'CN'")

        # sel_str = """SELECT conso.CUI, conso.AUI, conso.SAB, conso.CODE, lab.ITEMID, lab.LOINC_CODE"""
        # exec_str = f"INSERT INTO {tbl} {sel_str} from {j_str} limit {n}"
        exec_str = f"INSERT INTO {tbl} {j_str} limit {n}"
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
