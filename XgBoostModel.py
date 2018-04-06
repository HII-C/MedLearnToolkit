import MySQLdb as sql
from collections import defaultdict
from getpass import getpass
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.tree import ExtraTreeClassifier
from sklearn.metrics import accuracy_score
import xgboost as xg
import numpy as np

class XgBoostModel:
    def __init__(self, lhs_type, rhs_type):
        self.lhs_type = lhs_type
        self.rhs_type = rhs_type
        self.der_mimic_conn = None
        self.der_mimic_cur = None
        self.der_mimic_table = str
        self.universe_of_codes = dict()
        self.X_train, self.x_test, self.Y_train, self.y_test = (None, None, None, None)
        self.model = None
        self.target = str

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
        return(ret_list)

    def get_LHS_for_entry_matrix(self, patients):
        data_map = {"Condition": 0, "Observation": 1, "Medication": 2}
        # Do a dict of dict, with enties of inner dict being "{patient_id}": list(this_patients_records)
        entry_dict = {"Observation": defaultdict(list), "Condition": defaultdict(list)}
        print(f"Loaded {len(patients)} total patients, forming LHS of type {self.lhs_type} now.")
        # Hold the data_types NumPy arrays together but distinct and clearly identified
        dict_of_nparr = dict()
        
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
        # Copy the single instance of the dict, so we don't modify the base
        # Important not to reform 1k+ attributes for every patient (gets expensive)
        for pat_index, pat in enumerate(patients):
            pat_d = base_d.copy()
            for key in entry_dict[self.lhs_type][pat]:
                pat_d[key] = 1
            for index, val in enumerate(pat_d.values()):
                full_np_arr[pat_index][index] = val
        print("LHS for patient data matrix formed.")
        return full_np_arr
    
    def get_RHS_for_entry_matrix(self, patients, target):
        data_map = {"Condition": 0, "Observation": 1, "Medication": 2}
        print(f"Forming RHS of type {self.rhs_type} now.")
        self.target = target
        labels = defaultdict(lambda: 0)
        # target_col = list(self.universe_of_codes[target_type]).index(target)
        exec_str = f"""
                    SELECT SUBJECT_ID, CUI
                        FROM
                    derived.{self.der_mimic_table}
                        WHERE
                    SOURCE = {data_map[self.rhs_type]} and
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

    def init_xg_gtb(self, lhs_matrix, rhs_matrix):
        split_size = .010
        self.X_train, self.x_test, self.Y_train, self.y_test = train_test_split(lhs_matrix, rhs_matrix, test_size=split_size)
        print(f"Data split into {split_size} train:test. Creating model now.")
        d_train = xg.DMatrix(self.X_train, self.Y_train, feature_names=list(self.universe_of_codes[self.lhs_type]))
        param = {'max_depth':7, 'eta':.2, 'objective':'binary:logistic'}
        num_round = 4
        self.model = xg.train(param, d_train, num_round)
        print("Model creation is finished.")
    
    def prediction_acc(self):
        print("Predicting model accuracy over ")
        d_test = xg.DMatrix(self.x_test, self.y_test, feature_names=list(self.universe_of_codes[self.lhs_type]))
        y_pred = self.model.predict(d_test)
        preds = [round(value) for value in y_pred] 
        accuracy = accuracy_score(self.y_test, preds)
        print(f"Accuracy: {accuracy * 100.0}")
        #_, __ = self.logregobj(preds, d_test)
        #print(f'Gradient = {_}, hess = {__}')

    # def semrep_feat_select(self, lhs_matrix, rhs_matrix, lhs_type, rhs_type):

if __name__ == "__main__":
    example = XgBoostModel("Observation", "Condition")
    user = 'root'
    pw = getpass(f"What is the password for the user {user}\n")
    der_db = {'user': user, 'db': 'derived', 'host': 'db01.healthcreek.org', 'password': pw}
    example.connect_der_mimic_db(der_db, "patients_as_cui")
    example_patient_id_arr = example.get_patients(n=10000)
    lhs_returned = example.get_LHS_for_entry_matrix(example_patient_id_arr)
    condition_labels_for_target = example.get_RHS_for_entry_matrix(example_patient_id_arr, "C0375113")
    example.init_xg_gtb(lhs_returned, condition_labels_for_target)
