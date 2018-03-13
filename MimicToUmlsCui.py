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
        self.gen_conn = sql.connect(database)
        self.gen_cur = self.gen_conn.cursor()

    def connect_mimic_db(self, database):
        self.mimic_conn = sql.connect(database)
        self.mimic_cur = self.mimic_conn.cursor()

    def connect_umls_db(self, database):
        self.umls_conn = sql.connect(database)
        self.umls_cur = self.umls_conn.cursor()
        self.umls_table = "MRCONSO"

    def create_derived(self, n=10000):
        into = """ INTO ItemIdToCUI (CUI CHAR(8),
                                    AUI VARCHARl(9),
                                    SAB VARCHAR(40),
                                    CODE CHAR(100),
                                    ITEMID SMALLINT,
                                    LOINC_CODE VARCHAR(255))"""
        sel_str = " CUI, AUI, SAB, CODE, ITEMID, LOINC_CODE"
        from_str = " umls.MRCONSO, mimic.D_LABITEMS"
        where_str = """ where umls.MRCONSO.CODE = mimic.D_LABITEMS.LOINC_CODE
                    and umls.MRCONSO.LAT = 'ENG'
                    and umls.MRCONSO.TTY = 'CN'
                    and umsl.MRCONSO.SAB = 'LNC'
                    """
        exec_str = f"SELECT{into}{sel_str} from{from_str}{where_str} limit {n}"
        self.mimic_cur.execute(exec_str)

if __name__ == "__main__":
    print("Starting")
    # user = input("What is the user to access the databases?\n")
    user = 'greenes2018'
    pw = getpass(f'What is the password for the user {user}?\n')

    gen_db = {'user': user, 'db': None, 'host': 'db01.healthcreek.org', 'password': pw}
    mimic_db = {'user': user, 'db': 'mimic', 'host': 'db01.healthcreek.org', 'password': pw}
    umls_db = {'user': user, 'db': 'umls', 'host': 'db01.healthcreek.org', 'password': pw}

    example = MimicToUmlsCui()
    example.connect_gen_db(gen_db)
    example.create_derived()