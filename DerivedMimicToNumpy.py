import MySQLdb as sql
from collections import defaultdict
from getpass import getpass
from sklearn.cross_validation import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
import xgboost as xg
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
        data__map = {"Observation": 0, "Condition": 1, "Medication": 2}
        dict_of_nparr = dict()
        if type(data_types) is str:
            data_types = [data_types]
        for data_type_ in data_types:
            set_of_codes = set()
            code_by_patient = defaultdict(list)
            for pat in patients:
                self.der_mimic_cur.execute(
                    f"SELECT CODE FROM {self.der_mimic_table} WHERE SUBJECT_ID = {pat} and SOURCE = {data__map[data_type_]}")
                tmp = [*self.der_mimic_cur.fetchall()]
                code_by_patient[pat] = tmp
                set_of_codes = set(tmp) | set_of_codes

            self.universe_of_codes[data_type_] = set_of_codes
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
            dict_of_nparr[data_type_] = full_np_arr
        return dict_of_nparr

    def init_ML_model(self, data, target, target_dtype):
        labels = list()
        target_col = list(self.universe_of_codes[target_dtype]).index(target)
        for bin_exist in target[target_col]:
            labels.append(bin_exist)
        X_train, x_test, Y_train, y_test = train_test_split(data, labels)
        # xg_train = xg.DMatrix(x_train, y_train)
        # regr = xg.XGBClassifier(objective="binary:logistic")
        regr = GradientBoostingClassifier()
        regr.fit(X_train, Y_train)
        print(regr.feature_importances_[0:10])

if __name__ == "__main__":
    example = DerivedMimicToNumpy()
    user = 'root'
    pw = getpass(f"What is the password for the user {user}\n")
    der_db = {'user': user, 'db': 'derived', 'host': 'db01.healthcreek.org', 'password': pw}
    example.connect_der_mimic_db(der_db, "patients_as_cui")
    example_patient_id_arr = example.get_patients()
    example.get_entries_for_paitents(example_patient_id_arr, data_types=["Condition", "Observation"])
