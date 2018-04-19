import MySQLdb as sql
from collections import defaultdict
from getpass import getpass
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.tree import ExtraTreeClassifier
from sklearn.metrics import accuracy_score
import xgboost as xg
import numpy as np

class XgBoost:
    def __init__(self, lhs_type, rhs_type, target):
        self.der_mimic_conn = None
        self.der_mimic_cur = None
        self.der_mimic_table = None
        self.universe_of_codes = dict()
        self.target = target
        self.lhs_type = lhs_type
        self.rhs_type = rhs_type

    def connect_der_mimic_db(self, database, table_name):
        self.der_mimic_conn = sql.connect(**database)
        self.der_mimic_cur = self.der_mimic_conn.cursor()
        self.der_mimic_table = table_name

    def get_patients(self, n=1000):
        self.der_mimic_cur.execute(f"SELECT DISTINCT SUBJECT_ID FROM {self.der_mimic_table} limit {n}")
        ret_list = list()
        patients = self.der_mimic_cur.fetchall()
        # Have to do this because fetchall() returns a list of tuples
        for patient_id in patients:
            ret_list.append(patient_id[0])
        # We want a set of unique ID's, so we use "set" to ensure that
        return ret_list

    def get_LHS_for_entry_matrix(self, patients):
        data_map = {"Condition": 0, "Observation": 1, "Medication": 2}
        # Do a dict of dict, with enties of inner dict being "{patient_id}": list(this_patients_records)
        entry_dict = {"Observation": defaultdict(list), "Condition": defaultdict(list)}
        # Hold the data_types NumPy arrays together but distinct and clearly identified
        dict_of_nparr = dict()
        # So we can iterate even if the non-default input is just a string
        # Need to do few large instead of many small, aka CANNOT DO 1 PER PATIENT ID
        # Selects take a long time to process so we must minimize the number of them
        exec_str = f"""
                    SELECT SUBJECT_ID, CUI 
                        FROM 
                    derived.{self.der_mimic_table} 
                        WHERE 
                    SUBJECT_ID in {tuple(patients)} and 
                    SOURCE = {data_map[self.lhs_type]}"""
        self.der_mimic_cur.execute(exec_str)
        entries = self.der_mimic_cur.fetchall()
        self.universe_of_codes[self.lhs_type] = set([x[1] for x in entries])
        for entry in entries:
            entry_dict[self.lhs_type][entry[0]].append(entry[1])
        
        # Use X = codes, Y = patients, set dtype to smallest int since binary but int needed for ML
        full_np_arr = np.ndarray(shape=(len(patients),len(self.universe_of_codes[self.lhs_type])), dtype=np.int8)
        base_d = dict()
        for code in self.universe_of_codes[self.lhs_type]:
            base_d[code] = 0

        for pat_index, pat in enumerate(patients):
            pat_d = base_d.copy()
            for key in entry_dict[self.lhs_type][pat]:
                pat_d[key] = 1
            for index, val in enumerate(pat_d.values()):
                full_np_arr[pat_index][index] = val
        print(full_np_arr[0:5][0:10])
        print("NumPy arrays of patient data formed!")
        return full_np_arr
    
    def get_RHS_for_entry_matrix(self, patients):
        data_map = {"Condition": 0, "Observation": 1, "Medication": 2}
        labels = defaultdict(lambda: 0)
        # target_col = list(self.universe_of_codes[target_type]).index(target)
        exec_str = f"""
                    SELECT SUBJECT_ID, CUI
                        FROM
                    derived.{self.der_mimic_table}
                        WHERE
                    SOURCE = {data_map[self.rhs_type]} and
                    CUI = \"{self.target}\" and
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

    def init_xg_gtb(self, lhs_matrix, rhs_matrix):
        split_size = .5
        self.X_train, self.x_test, self.Y_train, self.y_test = train_test_split(lhs_matrix, rhs_matrix, test_size=split_size)
        d_train = xg.DMatrix(self.X_train, self.Y_train, feature_names=list(self.universe_of_codes[self.lhs_type]))
        param = {'max_depth':7, 'eta':.2, 'objective':'binary:logistic'}
        num_round = 4
        self.model = xg.train(param, d_train, num_round)
        # /////////////////////////////////////////////////////////////////////////////
        # regr = xg.XGBClassifier(objective="binary:logistic")
        # regr.fit(self.X_train, self.Y_train)
        # print(regr.feature_importances_)
        # y_pred = regr.predict(self.x_test)
        # preds = [round(value) for value in y_pred]
        # accuracy = accuracy_score(self.y_test, preds)
        # print(f"Accuracy in {len(self.x_test)} test cases = {accuracy * 100.0}")
        # /////////////////////////////////////////////////////////////////////////////
        print(f"Data split into {split_size} train:test. Creating model now.")
        print("Model creation is finished.")

    def prediction_acc(self):
        print(f"Predicting model accuracy over target: {self.target}")
        d_test = xg.DMatrix(self.x_test, self.y_test, feature_names=list(self.universe_of_codes[self.lhs_type]))
        y_pred = self.model.predict(d_test)
        preds = [round(value) for value in y_pred] 
        accuracy = accuracy_score(self.y_test, preds)
        print(f"Accuracy in {len(self.x_test)} test cases = {accuracy * 100.0}")

if __name__ == "__main__":
    example = XgBoost("Observation", "Condition", "C0375113")
    user = 'root'
    pw = getpass(f"What is the password for the user {user}\n")
    der_db = {'user': user, 'db': 'derived', 'host': 'db01.healthcreek.org', 'password': pw}
    example.connect_der_mimic_db(der_db, "patients_as_cui")
    example_patient_id_arr = example.get_patients(n=10000)
    observation_data = example.get_LHS_for_entry_matrix(example_patient_id_arr)
    condition_data = example.get_RHS_for_entry_matrix(example_patient_id_arr)
    example.init_xg_gtb(observation_data, condition_data)
    example.prediction_acc()