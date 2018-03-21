import MySQLdb as sql
from collections import defaultdict
import numpy as np

class DerivedMimicToNumpy:
    def __init__(self):
        self.der_mimic_conn = None
        self.der_mimic_cur = None
        self.der_mimic_table = None
        self.universe_of_codes = dict()

    def connect_der_mimic_db(self, database, table_name):
        self.der_mimic_conn = sql.connect(**database)
        self.der_mimic_cur = self.der_mimic_conn.cursor()
        self.der_mimic_table = table_name

    def get_patients(self, n=1000):
        self.der_mimic_cur.execute(f"SELECT DISTINCT PMID FROM {self.der_mimic_table} limit {n}")
        return([*self.der_mimic_cur.fetchall()])

    def get_entries_for_paitents(self, patients, data_types=["Condition", "Observation", "Medication"]):
        m_ = {"Condition": 1, "Observation": 0, "Medication": 2}
        dict_of_nparr = dict()
        if type(data_types) is str:
            data_types = [data_types]
        for ty in data_types:
            set_of_codes = set()
            code_by_patient = defaultdict(list)
            for pat in patients:
                self.der_mimic_cur.execute(
                    f"SELECT CODE FROM {self.der_mimic_table} WHERE SUBJECT_ID = {pat} and SOURCE = {m_[ty]}")
                tmp = [*self.der_mimic_cur.fetchall()]
                code_by_patient[pat] = tmp
                set_of_codes = set(tmp) | set_of_codes

            self.universe_of_codes[ty] = set_of_codes
            base_d = dict()
            # Use X = codes, Y = patients, set dtype to smallest int since binary but int needed for ML
            full_np_arr = np.ndarray(shape=(len(set_of_codes), len(patients)), dtype=np.int8)
            for code in set_of_codes:
                base_d[code] = 0

            for pat_index, pat in enumerate(patients):
                pat_d = base_d
                for key in code_by_patient[pat]:
                    pat_d[key] = 1
                for index, val in enumerate([*pat_d.values()]):
                    full_np_arr[index][pat_index] = val
            dict_of_nparr[ty] = full_np_arr
        return dict_of_nparr

if __name__ == "__main__":
    