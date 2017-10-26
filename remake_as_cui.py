import psycopg2
import numpy as np

class convert_to_cui(object):
    mimic_conn = psycopg2.connect("dbname='mimic' user='root' host='localhost' password='password'")
    mimic_cur = mimic_conn.cursor()

    umls_conn = psycopg2.connect("dbname='UMLS' user='root' host='localhost' password='password'")
    umls_cur = umls_conn.cursor()

    mimic_cui_conn = psycopg2.connect("dbname='mimic_cui' user='root' host='localhost' password='password'")
    mimic_cui_cur = mimic_cui_conn.connect()

    def __init__(self, diagnoses):
        self.diagnoses = diagnoses

    def mimic_cui_table_init(self):
        query_str = "SELECT * from mimic_cui.tables;"
        self.mimic_cui_cur.execute(query_str)
        tables = self.mimic_cui_cur.fetchall()
        if 'by_visit' not in tables:
            table_creation_str = 'CREATE table by_visit (hadm_id int, condition_json JSON, observation_json JSON, treatment_json JSON);'
            self.mimic_cui_cur.execute(table_creation_str)

    def loinc_to_cui_visit(self, size_):
        query_str = ('SELECT (hadm_id, itemid, value, flag) FROM mimiciii.LABEVENTS limit {};').format(size_)
        self.mimic_cur.execute(query_str)
        labevents = self.mimic_cur.fetchall()
        converting_to_cui_dict = dict()

        for item in labevents:
            try:
                x = converting_to_cui_dict[item[1]]
            except KeyError as key_err:
                loinc_query_str = ('SELECT (loinc_code) from mimiciii.D_LABITEMS where ITEMID = {} limit 1;')
                self.mimic_cur.execute(loinc_query_str)
                loinc_query_response = self.mimic_cur.fetchall()
                converting_to_cui_dict[item[1]] = int(loinc_query_response[0])
        
        for item in converting_to_cui_dict.keys():
            # UMLS query ('SELECT (CUI) from )