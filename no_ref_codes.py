import numpy as np
import psycopg2
import pymysql
from sklearn import (ensemble, feature_selection, linear_model, neural_network,
                     svm, tree)
from sklearn.linear_model import LogisticRegression

# NOTE: Look at potientally implementing GridSearchCV in the future
# from sklearn.model_selection import GridSearchCV

class no_umls_codes():
    conn = pymysql.connect(user='root', host='db01.healthcreek.org',db='mimic',password='HealthCreekMySQLr00t')
    cur = conn.cursor()

    def __init__(self, target):
        self.target = target


    # NOTE: Only used as we don't have static code dictionaries (LOINC, SNOMED, etc) loaded to @general right now
    def code_generation(self, mapping_from, query_size, from_index, db_features, flag):
        patient_matrix = {}
        code_dict = {}
        query_string = ("SELECT {0} from {1} ORDER BY RAND() limit {2};").format(db_features, mapping_from, query_size)
        self.cur.execute(query_string)
        rows = self.cur.fetchall()
        visit_matrix = {}
        for row in rows:
            if flag == False:
                query_val = row[from_index]
            else:
                query_val = tuple([row[from_index], row[from_index+1]])
            # row[0] = patient_id, row[1] = visit_id, row[3+] = queries
            if row[0] in visit_matrix:
                patient_matrix[row[0]].append(query_val)
                if row[1] in visit_matrix[row[0]]:
                    if (query_val in code_dict):
                        visit_matrix[row[0]][row[1]].append(query_val)
                    else:
                        if (query_val not in self.target):
                            code_dict[query_val] = query_val
                        visit_matrix[row[0]][row[1]].append([query_val])
                else:
                    visit_matrix[row[0]][row[1]] = [query_val]
            else:
                patient_matrix[row[0]] = [query_val]
                visit_matrix[row[0]] = dict()
                visit_matrix[row[0]][row[1]] = [query_val]
        self.code_dict = code_dict
        self.patient_matrix = patient_matrix
        self.visit_matrix = visit_matrix


    # Generates a sparse attribute matrix based on HADM_ID's, higher resolution than patient, but might to "too much"
    def sparse_matrix_generation_by_visit(self):
        visit_sparse_matrix = dict()

        for patient_id in self.patient_matrix:
            for visit_id in self.visit_matrix[patient_id]:
                visit_sparse_matrix[visit_id] = []
                for code in self.code_dict:
                    if code in self.visit_matrix[patient_id][visit_id]:
                        visit_sparse_matrix[visit_id].append(1)
                    else:
                        visit_sparse_matrix[visit_id].append(0)
        return visit_sparse_matrix


    # Generates a sparse attribute matrix by subject_id, less resolution but perhaps more "whole" picture
    # NOTE: Both _visit and _patient need to be evalutated to know which is better
    # We should explore creating a standard measure of success once we start training in earnest
    def sparse_matrix_generation_by_patient(self):
        patient_sparse_matrix = dict()
        # print(self.patient_matrix)
        for patient_id in self.patient_matrix:
            patient_sparse_matrix[patient_id] = []
            for code in self.code_dict:
                if code in self.patient_matrix[patient_id]:
                    patient_sparse_matrix[patient_id].append(1)
                else:
                    patient_sparse_matrix[patient_id].append(0)
        return patient_sparse_matrix


    # Creating the data structures needed for any regression/ML @ the visit resolution
    # NOTE: We use contiguious blocks of memory with NumPy, this is crucial for performance
    def array_generation_for_ml_visit(self, mapping_to, visit_matrix, db_features):
        string_tuple = list()
        for x in visit_matrix.keys():
            try:
                if x != None:
                    string_tuple.append(str(x))
            except TypeError as te:
                print(te)
                print(visit_matrix.keys())
                print(x)
        string_tuple = tuple(string_tuple)
        query_string = ("SELECT {0} from {1} WHERE hadm_id in {2}").format(db_features, mapping_to, string_tuple)
        self.cur.execute(query_string)
        target_rows = self.cur.fetchall()
        target_dict = {}
        for item in target_rows:
            if item[1] in target_dict:
                target_dict[item[1]].append(item[2])
            else:
                target_dict[item[1]] = [item[2]]

        X = np.zeros(shape=(len(target_dict.keys()), len(self.code_dict.keys())))
        y = np.zeros(shape=(len(target_dict.keys())))

        count_y = 0
        for item in target_dict:
            X[count_y] = np.array(visit_matrix[item])
            for tar in self.target:
                if (tar in target_dict[item]):
                    y[count_y] = 1
                else:
                    y[count_y] = 0
                    break
            count_y += 1
        return X, y


    # Creating the data structures needed for any regression/ML @ the patient resolution
    # NOTE: We use contiguious blocks of memory with NumPy, this is crucial for performance
    def array_generation_for_ml_patient(self, mapping_to, patient_matrix, db_features):
        string_tuple = list()
        for x in patient_matrix.keys():
            string_tuple.append(int(x))
        string_tuple = tuple(string_tuple)
        query_string = ("SELECT {0} from {1} WHERE subject_id in {2}").format(db_features, mapping_to, string_tuple)
        self.cur.execute(query_string)
        target_dict = {}
        target_rows = self.cur.fetchall()
        for item in target_rows:
            if item[0] in target_dict:
                target_dict[item[0]].append(item[2])
            else:
                target_dict[item[0]] = [item[2]]

        X = np.zeros(shape=(len(target_dict.keys()), len(self.code_dict.keys())))
        y = np.zeros(shape=(len(target_dict.keys())))
        # X = [[0]*len(self.code_dict.keys())]*len(target_dict.keys())
        # y = [0]*len(target_dict.keys())

        for index, item in enumerate(target_dict.keys()):
            X[index] = patient_matrix[item]
            for tar in self.target:
                if (tar in target_dict[item]):
                    y[index] = 1
                elif y[index] != 1:
                    y[index] = 0
        return X, y

    def minimize_ml_attributes(self, X):
        for index, value in X[0]:
            remove_flag = True
            for i in range(0, len(X)):
                if X[i][index] == 1:
                    remove_flag = False
            if remove_flag == True:
                for i in range(0, len(X)):
                    del X[i][index]
        for i in range(0, len(X)):
            X[i] = tuple(X[i])
        X = np.asarray(X)
        return X

    # Logisitic Regression using Lasso optimization and Lars algorithm
    # New, important topics: One-hot encoding
    # http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html
    def learning_by_target_lasso(self, X, y, alpha, input_c=None):
        # alphas = np.logspace(-3, 0, 20)
        print(("Finding the most important half of {} features").format(len(X[0])))
        regr = linear_model.LogisticRegression(penalty="l2", C=input_c, n_jobs=-1, solver="newton-cg")
        rfe = feature_selection.RFE(regr)
        rfe.fit(X, y)
        new_dict = dict()
        for index, code in enumerate(list(self.code_dict)):
            # new_dict[code] = regr.coef_[0][index]
            new_dict[code] = rfe.ranking_[index]
        return new_dict

    # Logisitic Regression using Cross-validation for alphas, hence no fit->score iteration like in lasso
    # def learning_by_target_logisticCV(self, X, y):
    #     regr = linear_model.LogisticRegressionCV()
    #     regr.fit(X,y)
    #     return regr.coef_[0]

    
    # Preserves and orders codes by values, though keys come from scoring matrix, so identical keys 
    # (ex. {1, 0, 0, -1}, 0 is clearly duplicate) will map to 1 value (Condition/Observation code)
    # In all cases I can think of this is inconsequential (non-integer values are floats which)
    # have almost 0 chance of being identical, esp for the crucial in regression which are what we care about.
    def order_output_matrix(self, _list):
        _dict = dict()
        count = 0
        return ((sorted(_list.items(), key=lambda x: x[1]))[::-1], _list)
        #for item in self.code_dict.keys():
        #    _dict[_list[count]] = item
        #    count += 1
        # _list.sort()
        #return(_list, _dict)
