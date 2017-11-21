import psycopg2
import pymysql
import numpy as np

class convert_to_cui(object):

    def __init__(self):
        self.mimic_conn = psycopg2.connect("dbname='mimic' user='root' host='db01.healthcreek.org' password='Sup3r p0n13s'")
        self.mimic_cur = self.mimic_conn.cursor()

    def create_translation_db(self, host_, user_, password_, name_, delete_):
        self.connection = pymysql.connect(host=host_, user=user_, password=password_)
        self.cursor = self.connection.cursor()

        search_str = ("SHOW DATABASES LIKE {};").format(name_)
        if (name_ not in self.cursor.execute(search_str).fetchall()):
            exec_str = ("CREATE DATABASE {};").format(name_)
            self.cursor.execute(exec_str)
            # iid, loinc_code, cui
            exec_str = ("CREATE TABLE {}.itemid_to_cui (iid MEDIUMINT UNSIGNED NOT NULL, cui char(8) UNIQUE, loinc_code char(7) UNIQUE, PRIMARY KEY(iid)) ENGINE = MYISAM;").format(name_)
            self.cursor.execute(exec_str)
        


    def mimic_cui_obs_table_init(self, db_name):
        query_str = ("SELECT * from {}.tables;").format(db_name)
        if ('by_visit' not in self.cursor.execute(query_str).fetchall()):
            print('Here')
            # hadm_id, cui, value, valuenom, valueuom, flag
            table_creation_str = ('CREATE TABLE {}.mimic_cui_obs (hadm_id MEDIUM UNSIGNED NOT NULL, cui char(8), value VARCHAR(200), valuenum double precision, valueuom VARCHAR(20), flag VARCHAR(20), key(hadm_id), key(cui));').format(db_name)
            self.cursor.execute(table_creation_str)
    
    def iid_to_loinc(self, mimic_db_name_):
        query_str = ('SELECT DISTINCT ITEMID, loinc_code FROM {}.D_LABITEMS;').format(mimic_db_name_)
        iid_lionc_array = [list(), list()]
        for item in (self.mimic_conn.execute(query_str).fetchall()):
            iid_lionc_array[0].append[int(item[0])]
            iid_lionc_array[1].append[str(item[1])]
        insert_bulk_str = ('INSERT into {0}.itemid_to_cui (iid, loinc_code) values {1}, {2};').format(mimic_db_name_, \
            tuple(iid_lionc_array[0]), tuple(iid_lionc_array[1]))

        # Disabling keys during bulk insert gives considerable speedup
        # https://dev.mysql.com/doc/refman/5.7/en/alter-table.html
        self.cursor.execute(("ALTER TABLE {0}.itemid_to_cui DISABLE KEYS;").format(mimic_db_name_))
        self.cursor.execute(insert_bulk_str)
        self.cursor.execute(("ALTER TABLE {0}.itemid_to_cui ENABLE KEYS;").format(mimic_db_name_))

    def loinc_to_cui_visit(self, mimic_db_name_, umls_mt_, derived_db_):
        retrieval_string = ('select (CUI, CODE) from {0}.MRCONSO WHERE STT = "PF" AND TS = "P" AND ISPREF = "Y" AND LAT = "ENG" AND SAB="LNC";').format(umls_mt_)

        

            # insert into itemid_to_cui iid, cui select DISTINCT ITEMID, loinc_code from {}.D_LABITEMS, loinc l where 