import psycopg2
import numpy as np
from sklearn import linear_model
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV


# NOTE: Look at potientally implementing GridSearchCV in the future
# from sklearn.model_selection import GridSearchCV

class no_ref_codes():
    inp = input("Enter PostGRES password now.")
    conn = psycopg2.connect(("dbname='mimic' user='postgres' host='db01.healthcreek.org' password={}").format(inp))
    cur = conn.cursor()

    def __init__(self, diagnoses):
        self.diagnoses = diagnoses

    
    # NOTE: Only used as we don't have static code dictionaries (LOINC, SNOMED, etc) loaded to @general right now
    def code_generation(self, query_size):
        patient_matrix = {}
        code_dict = {}
        query_string = ("SELECT * from mimiciii.INPUTEVENTS_MV ORDER BY RAND() limit {};").format(query_size)
        self.cur.execute(query_string)
        rows = self.cur.fetchall()
        visit_matrix = {}
        visit_count = 0
        for row in rows:
            # row[1] = patient_id, row[2] = visit_id, row[4] = icd_9_code
            if row[1] in visit_matrix:
                patient_matrix[row[1]].append(row[6])
                if row[2] in visit_matrix[row[1]]:
                    if (row[6] in code_dict:
                        visit_matrix[row[1]][row[2]].append(row[6])
                    else:
                        code_dict[row[6]] = row[6]
                        visit_matrix[row[1]][row[2]].append([row[6]])
                else:
                    visit_matrix[row[1]][row[2]] = [row[6]]
            else:
                patient_matrix[row[1]] = [row[6]]
                visit_matrix[row[1]] = {row[2]: [row[6]]}
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
    def array_generation_for_ml_visit(self, visit_matrix):
        string_tuple = list()
        for x in visit_matrix:
            string_tuple.append(int(x))
        string_tuple = tuple(string_tuple)

        query_string = ("SELECT * from mimiciii.DIAGNOSES_ICD WHERE hadm_id in {}").format(string_tuple)
        self.cur.execute(query_string)
        diagnoses_rows = self.cur.fetchall()
        diagnoses_dict = {}
        for item in diagnoses_rows:
            if item[2] in diagnoses_dict:
                diagnoses_dict[item[2]].append(item[4])
            else:
                diagnoses_dict[item[2]] = [item[4]]

        X = np.zeros(shape=(len(diagnoses_dict.keys()), len(self.code_dict.keys())))
        y = np.zeros(shape=(len(diagnoses_dict.keys())))

        count_y = 0
        for item in diagnoses_dict:
            X[count_y] = np.array(visit_matrix[item])
            if (self.diagnoses in diagnoses_dict[item]):
                y[count_y] = 1
            else:
                y[count_y] = 0
            count_y += 1
        return X, y


    # Creating the data structures needed for any regression/ML @ the patient resolution
    # NOTE: We use contiguious blocks of memory with NumPy, this is crucial for performance
    def array_generation_for_ml_patient(self, patient_matrix):
        string_tuple = list()
        for x in patient_matrix.keys():
            string_tuple.append(int(x))
        string_tuple = tuple(string_tuple)

        query_string = ("SELECT * from mimiciii.DIAGNOSES_ICD WHERE subject_id in {}").format(string_tuple)
        self.cur.execute(query_string)
        diagnoses_rows = self.cur.fetchall()
        diagnoses_dict = {}
        for item in diagnoses_rows.keys():
            if item[1] in diagnoses_dict:
                diagnoses_dict[item[1]].append(item[4])
            else:
                diagnoses_dict[item[1]] = [item[4]]

        X = np.zeros(shape=(len(diagnoses_dict.keys()), len(self.code_dict.keys())))
        y = np.zeros(shape=(len(diagnoses_dict.keys())))

        count_y = 0
        for item in diagnoses_dict.keys():
            X[count_y] = np.array(patient_matrix[item])
            if (self.diagnoses in diagnoses_dict[item]):
                y[count_y] = 1
            else:
                y[count_y] = 0
            count_y += 1
        return X, y


    # Logisitic Regression using Lasso optimization and Lars algorithm
    def learning_by_diagnoses_lasso(self, X, y):
        alphas = np.logspace(-4, -1, 10)
        regr = linear_model.LassoLars()
        scores = [regr.set_params(alpha=alpha).fit(X, y).score(X, y) for alpha in alphas]    
        best_alpha = alphas[scores.index(max(scores))]
        regr.alpha = best_alpha
        regr.fit(X, y)
        return regr.coef_

    # Logisitic Regression using Cross-validation for alphas, hence no fit->score iteration like in lasso
    def learning_by_diagnoses_logisticCV(self, X, y):
        regr = linear_model.LogisticRegressionCV()
        regr.fit(X,y)
        return regr.coef_[0]

    
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
