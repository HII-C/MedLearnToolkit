import MySQLdb as sql
from collections import defaultdict
from getpass import getpass
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.tree import ExtraTreeClassifier
from sklearn.metrics import accuracy_score
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
        self.der_mimic_cur.execute(f"SELECT DISTINCT SUBJECT_ID FROM {self.der_mimic_table} limit {n}")
        ret_list = list()
        patients = self.der_mimic_cur.fetchall()
        print(len(patients))
        # Have to do this because fetchall() returns a list of tuples
        for patient_id in patients:
            ret_list.append(patient_id[0])
        # We want a set of unique ID's, so we use "set" to ensure that
        return(ret_list)

    def get_LHS_for_entry_matrix(self, patients, data_types=["Condition", "Observation", "Medication"]):
        data_map = {"Observation": 0, "Condition": 1, "Medication": 2}
        # Do a dict of dict, with enties of inner dict being "{patient_id}": list(this_patients_records)
        entry_dict = {"Observation": defaultdict(list), "Condition": defaultdict(list)}
        print(len(patients))
        # Hold the data_types NumPy arrays together but distinct and clearly identified
        dict_of_nparr = dict()
        # So we can iterate even if the non-default input is just a string
        if type(data_types) is str:
            data_types = [data_types] 
        for data_type_ in data_types:
            # Need to do few large instead of many small, aka CANNOT DO 1 PER PATIENT ID
            # Selects take a long time to process so we must minimize the number of them
            exec_str = f"""
                        SELECT SUBJECT_ID, CUI 
                            FROM 
                        derived.{self.der_mimic_table} 
                            WHERE 
                        SUBJECT_ID in {tuple(patients)} and 
                        SOURCE = {data_map[data_type_]}"""
            self.der_mimic_cur.execute(exec_str)
            entries = self.der_mimic_cur.fetchall()
            self.universe_of_codes[data_type_] = set([x[1] for x in entries])
            for entry in entries:
                entry_dict[data_type_][entry[0]].append(entry[1])
            
            # Use X = codes, Y = patients, set dtype to smallest int since binary but int needed for ML
            full_np_arr = np.ndarray(shape=(len(patients),len(self.universe_of_codes[data_type_])), dtype=np.int8)
            base_d = dict()
            for code in self.universe_of_codes[data_type_]:
                base_d[code] = 0

            for pat_index, pat in enumerate(patients):
                pat_d = base_d.copy()
                for key in entry_dict[data_type_][pat]:
                    pat_d[key] = 1
                for index, val in enumerate(pat_d.values()):
                    full_np_arr[pat_index][index] = val
            dict_of_nparr[data_type_] = full_np_arr
            print(full_np_arr[0:5][0:10])
        print("NumPy arrays of patient data formed!")
        return dict_of_nparr
    
    def get_RHS_for_entry_matrix(self, patients, target, target_type):
        data_map = {"Observation": 0, "Condition": 1, "Medication": 2}
        labels = defaultdict(lambda: 0)
        # target_col = list(self.universe_of_codes[target_type]).index(target)
        exec_str = f"""
                    SELECT SUBJECT_ID, CUI
                        FROM
                    derived.{self.der_mimic_table}
                        WHERE
                    SOURCE = {data_map[target_type]} and
                    CUI = \"{target}\" and
                    SUBJECT_ID in {tuple(patients)}
                    """
        self.der_mimic_cur.execute(exec_str)
        dirty_labels = self.der_mimic_cur.fetchall()
        for lbl in dirty_labels:
            labels[lbl[0]] = 1
        # This is necessary because ordering is not guaranteed w/ defaultdict && MySQL
        #                       (ESP WHEN THEY ARE COMBINED)
        ret_list = list()
        for patient in patients:
            ret_list.append(labels[patient])
        print("Right hand side of matrix formed")
        return ret_list

    def logregobj(self, preds, dtrain):
        labels = dtrain.get_label()
        preds = 1.0 / (1.0 + np.exp(-preds))
        grad = preds - labels
        hess = preds * (1.0 - preds)
        return grad, hess

    def init_ML_model(self, data, labels):
        print(f'Lenght of patient data {len(data)}')
        print(f'Lenght of label data {len(labels)}')
        # regr = xg.XGBClassifier(objective="binary:logistic")
        # regr.fit(X_train, Y_train)
        # y_pred = regr.predict(x_test)
        # predictions = [round(value) for value in y_pred]
        # accuracy = accuracy_score(y_test, y_pred)
        # print(f"Accuracy: {accuracy * 100.0}")
        X_train, x_test, Y_train, y_test = train_test_split(data, labels)
        d_train = xg.DMatrix(X_train, Y_train)
        d_test = xg.DMatrix(x_test, y_test)
        param = {'max_depth':2, 'eta':1, 'silent':1, 'objective':'binary:logistic'}
        num_round = 4
        bst = xg.train(param, d_train, num_round)
        preds = bst.predict(d_test)
        _, __ = self.logregobj(preds, d_test)
        print(f'Gradient = {_}, hess = {__}')

if __name__ == "__main__":
    example = DerivedMimicToNumpy()
    user = 'root'
    pw = getpass(f"What is the password for the user {user}\n")
    der_db = {'user': user, 'db': 'derived', 'host': 'db01.healthcreek.org', 'password': pw}
    example.connect_der_mimic_db(der_db, "patients_as_cui")
    example_patient_id_arr = example.get_patients()
    dict_returned = example.get_LHS_for_entry_matrix(example_patient_id_arr, data_types=["Observation"])
    observation_data = dict_returned["Observation"]
    condition_labels_for_target = example.get_RHS_for_entry_matrix(example_patient_id_arr,
                                                                   "C0011849",
                                                                   "Condition")
    example.init_ML_model(observation_data, condition_labels_for_target)
