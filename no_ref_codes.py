import psycopg2
import numpy as np
from sklearn import linear_model
from sklearn.linear_model import LogisticRegression


# NOTE: Look at potientally implementing GridSearchCV in the future
# from sklearn.model_selection import GridSearchCV

class no_ref_codes():
    conn = psycopg2.connect(("dbname='mimic' user='postgres' host='db01.healthcreek.org' password='Super p0n13s'"))
    cur = conn.cursor()

    def __init__(self, target):
        self.target = target

    
    # NOTE: Only used as we don't have static code dictionaries (LOINC, SNOMED, etc) loaded to @general right now
    def code_generation(self, mapping_from, query_size, from_index):
        patient_matrix = {}
        code_dict = {}
        query_string = ("SELECT * from mimiciii.{} ORDER BY RANDOM() limit {};").format(mapping_from, query_size)
        self.cur.execute(query_string)
        rows = self.cur.fetchall()
        visit_matrix = {}
        visit_count = 0
        for row in rows:
            # row[1] = patient_id, row[2] = visit_id, row[3] = itemid
            if row[1] in visit_matrix:
                patient_matrix[row[1]].append(row[from_index])
                if row[2] in visit_matrix[row[1]]:
                    if (row[3] in code_dict):
                        visit_matrix[row[1]][row[2]].append(row[from_index])
                    else:
                        code_dict[row[from_index]] = row[from_index]
                        visit_matrix[row[1]][row[2]].append([row[from_index]])
                else:
                    visit_matrix[row[1]][row[2]] = [row[from_index]]
            else:
                patient_matrix[row[1]] = [row[from_index]]
                visit_matrix[row[1]] = {row[2]: [row[from_index]]}
        self.code_dict = code_dict
        self.patient_matrix = patient_matrix
        self.visit_matrix = visit_matrix


    # Generates a sparse attribute matrix based on HADM_ID's, higher resolution than patient, but might to "too much"
    def sparse_matrix_generation_by_visit(self):
        visit_sparse_matrix = dict()
        visit_count = 0

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
    def array_generation_for_ml_visit(self, mapping_to, visit_matrix):
        string_tuple = list()
        for x in visit_matrix:
            string_tuple.append(int(x))
        string_tuple = tuple(string_tuple)
        query_string = ("SELECT * from mimiciii.{} WHERE hadm_id in {}").format(mapping_to, string_tuple)
        self.cur.execute(query_string)
        target_rows = self.cur.fetchall()
        target_dict = {}
        for item in target_rows:
            if item[2] in target_dict:
                target_dict[item[2]].append(item[4])
            else:
                target_dict[item[2]] = [item[4]]

        X = np.zeros(shape=(len(target_dict.keys()), len(self.code_dict.keys())))
        y = np.zeros(shape=(len(target_dict.keys())))

        count_y = 0
        for item in target_dict:
            X[count_y] = np.array(visit_matrix[item])
            if (self.target in target_dict[item]):
                y[count_y] = 1
            else:
                y[count_y] = 0
            count_y += 1
        return X, y


    # Creating the data structures needed for any regression/ML @ the patient resolution
    # NOTE: We use contiguious blocks of memory with NumPy, this is crucial for performance
    def array_generation_for_ml_patient(self, mapping_to, patient_matrix):
        string_tuple = list()
        for x in patient_matrix.keys():
            string_tuple.append(int(x))
        string_tuple = tuple(string_tuple)

        query_string = ("SELECT * from mimiciii.{} WHERE subject_id in {}").format(mapping_to, string_tuple)
        self.cur.execute(query_string)
        target_rows = self.cur.fetchall()
        target_dict = {}
        for item in target_rows:
            if item[1] in target_dict:
                target_dict[item[1]].append(item[4])
            else:
                target_dict[item[1]] = [item[4]]

        X = np.zeros(shape=(len(target_dict.keys()), len(self.code_dict.keys())))
        y = np.zeros(shape=(len(target_dict.keys())))

        count_y = 0
        for item in target_dict.keys():
            X[count_y] = np.array(patient_matrix[item])
            if (self.target in target_dict[item]):
                y[count_y] = 1
            else:
                y[count_y] = 0
            count_y += 1
        return X, y


    # Logisitic Regression using Lasso optimization and Lars algorithm
    def learning_by_target_lasso(self, X, y):
        alphas = np.logspace(-4, -1, 10)
        regr = linear_model.LassoLars()
        scores = [regr.set_params(alpha=alpha).fit(X, y).score(X, y) for alpha in alphas]    
        best_alpha = alphas[scores.index(max(scores))]
        regr.alpha = best_alpha
        regr.fit(X, y)
        return regr.coef_

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
        for item in self.code_dict.keys():
            _dict[_list[count]] = item
            count += 1
        _list.sort()
        return(_list[::-1], _dict)
