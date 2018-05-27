from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.tree import ExtraTreeClassifier
from sklearn.metrics import accuracy_score
from collections import defaultdict
from getpass import getpass
from PatientDataWrapper import PatientRecords
import MySQLdb as sql
import xgboost as xg
import numpy as np
import random


class XgBoost:
    def __init__(self, lhs_type, rhs_type, target):
        self.der_mimic_conn = None
        self.der_mimic_cur = None
        self.der_mimic_table = None
        self.universe_of_codes = dict()
        self.target = target
        self.lhs_type = lhs_type
        self.rhs_type = rhs_type
        self.patient_index_table = None

    def logregobj(self, preds, dtrain):
        labels = dtrain.get_label()
        preds = 1.0 / (1.0 + np.exp(-preds))
        grad = preds - labels
        hess = preds * (1.0 - preds)
        return grad, hess

    def init_xg_gtb(self, lhs_matrix, rhs_matrix):
        split_size = .5
        self.X_train, self.x_test, self.Y_train, self.y_test = train_test_split(
            lhs_matrix, rhs_matrix, test_size=split_size)
        print(f"Data split into {split_size} train:test. Creating model now.")
        d_train = xg.DMatrix(self.X_train, self.Y_train, feature_names=list(
            self.universe_of_codes[self.lhs_type]))
        param = {'max_depth': 4, 'eta': .1, 'objective': 'binary:logistic'}
        num_round = 4
        self.model = xg.train(param, d_train, num_round)

        print("Model creation is finished.")

    def prediction_acc(self):
        print(f"Predicting model accuracy over target: {self.target}")
        d_test = xg.DMatrix(self.x_test, self.y_test, feature_names=list(
            self.universe_of_codes[self.lhs_type]))
        y_pred = self.model.predict(d_test)
        preds = [round(value) for value in y_pred]
        accuracy = accuracy_score(self.y_test, preds)
        print(
            f"Accuracy in {len(self.x_test)} test cases = {accuracy * 100.0}")
        return accuracy

    def store_model_output(self):
        # Formal database outline for API input at "Example ML output" in the team drive
        attrib_dict = self.model.get_score(importance_type='gain')
        for key in list(attrib_dict.keys()):
            print(f"{key}: {attrib_dict[key]}")


if __name__ == "__main__":
    example = XgBoost("Observation", "Condition", "C0375113")
    # user = input("Input your user account")
    user = 'root'
    pw = getpass(f"Enter password for: {user}\n")
    der_db = {'user': user, 'db': 'derived',
              'host': 'db01.healthcreek.org', 'password': pw}
    patients = PatientRecords()
    lhs_matrix, rhs_matrix = patients.get_patients(
        der_db, 'patients_as_cui', 10000, "Condition", "Condition", "C0375113")
    example.init_xg_gtb(lhs_matrix, rhs_matrix)
    example.prediction_acc()
    example.store_model_output()
