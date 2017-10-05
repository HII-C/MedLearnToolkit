import math
import psycopg2
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn.model_selection import GridSearchCV, KFold
from sklearn import linear_model
from sklearn import svm
import numpy as np
import scipy


class no_ref_codes():
    diagnoses = ''
    def __init__(self, diagnoses):
        self.diagnoses = diagnoses
    
    conn = psycopg2.connect("dbname='mimic' user='student' host='localhost' password='password'")
    cur = conn.cursor()
    code_dict = dict()
    patient_matrix = dict()
    visit_matrix = dict()

    def code_generation(self, query_size):
        patient_matrix = {}
        code_dict = {}
        query_string = ("SELECT * from mimiciii.INPUTEVENTS_MV limit {};").format(query_size)
        self.cur.execute(query_string)
        rows = self.cur.fetchall()
        visit_matrix = {}
        visit_count = 0
        for row in rows:
            # row[1] = patient_id, row[2] = visit_id, row[4] = icd_9_code
            if row[1] in patient_matrix.keys():
                if row[2] in patient_matrix[row[1]].keys():
                    if (row[6] in code_dict.keys()):
                        patient_matrix[row[1]][row[2]].append(row[4])
                    else:
                        code_dict[row[6]] = row[6]
                        patient_matrix[row[1]][row[2]].append([row[6]])
                else:
                    patient_matrix[row[1]][row[2]] = [row[6]]
            else:
                patient_matrix[row[1]] = {row[2]: [row[6]]}
        self.code_dict = code_dict
        self.patient_matrix = patient_matrix


    def sparse_matrix_generation_by_visit(self):
        visit_sparse_matrix = dict()
        visit_count = 0

        for patient_id in self.patient_matrix.keys():
            for visit_id in self.patient_matrix[patient_id].keys():
                visit_sparse_matrix[visit_id] = []
                for code in self.code_dict.keys():
                    if code in self.patient_matrix[patient_id][visit_id]:
                        visit_sparse_matrix[visit_id].append(1)

                    else:
                        visit_sparse_matrix[visit_id].append(0)
        return visit_sparse_matrix


    def sparse_matrix_generation_by_patient(self):
        patient_sparse_matrix = dict()
        for patient_id in self.patient_matrix.keys():
            patient_sparse_matrix[patient_id] = []
            for code in self.code_dict.keys():
                if code in self.patient_matrix[patient_id]:
                    patient_sparse_matrix[patient_id].append(1)
                else:
                    patient_sparse_matrix[patient_id].append(0)
        return patient_sparse_matrix


    def array_generation_for_ml_visit(self, visit_matrix):
        string_tuple = list()
        for x in visit_matrix.keys():
            string_tuple.append(int(x))
        string_tuple = tuple(string_tuple)

        query_string = ("SELECT * from mimiciii.DIAGNOSES_ICD WHERE hadm_id in {}").format(string_tuple)
        self.cur.execute(query_string)
        diagnoses_rows = self.cur.fetchall()
        diagnoses_dict = {}
        for item in diagnoses_rows:
            if item[2] in diagnoses_dict.keys():
                diagnoses_dict[item[2]].append(item[4])
            else:
                diagnoses_dict[item[2]] = [item[4]]

        X = np.zeros(shape=(len(diagnoses_dict.keys()), len(self.code_dict.keys())))
        y = np.zeros(shape=(len(diagnoses_dict.keys())))

        count_y = 0
        for item in diagnoses_dict.keys():
            X[count_y] = np.array(visit_matrix[item])
            if (self.diagnoses in diagnoses_dict[item]):
                y[count_y] = 1
            else:
                y[count_y] = 0
            count_y += 1
        return X, y

    def learning_by_diagnoses_lasso(self, X, y, query_size):
        alphas = np.logspace(-4, -1, 15)
        regr = linear_model.LassoLars()
        scores = [regr.set_params(alpha=alpha).fit(X, y).score(X, y) for alpha in alphas]    
        best_alpha = alphas[scores.index(max(scores))]
        regr.alpha = best_alpha
        regr.fit(X, y)
        query_string = ("SELECT * from mimiciii.DIAGNOSES_ICD WHERE icd9_code = \'{}\' limit {};").format(self.diagnoses, query_size)
        self.cur.execute(query_string)
        prediction_rows = self.cur.fetchall()
        
        for row in prediction_rows:
            if (row[2] not in self.visit_matrix.keys()):
                self.cur.execute(("SELECT * from mimiciii.INPUTEVENTS_MV WHERE hadm_id = \'{}\';").format(row[2]))
                rows = self.cur.fetchall()
                this_patient = list()
                for r in rows:
                    this_patient.append(r[6])

                for r in rows:
                    vis_arr = []
                    for code in self.code_dict.keys():
                        if code in this_patient:
                            vis_arr.append(1)
                        else:
                            vis_arr.append(0)
                print('Should only show once') 
                print(regr.predict(np.array(vis_arr).reshape(1, -1)))
                exit()

    def learning_by_diagnoses_logisticCV(self, X, y):
        regr = linear_model.LogisticRegressionCV()
        regr.fit(X,y)
        return regr.coef_



testing = no_ref_codes('25000')
testing.code_generation(10000)
visit_sparse = testing.sparse_matrix_generation_by_visit()
test1, test2 = testing.array_generation_for_ml_visit(visit_sparse)
_list = testing.learning_by_diagnoses_logisticCV(test1, test2)
_dict = dict()
count = 0
for item in testing.code_dict.keys():
    _dict[_list[0][count]] = item
    count += 1
_list.sort()
new_list = _list[0][::-1]
print(new_list)
print(new_list[:5])
for item in new_list[:5]:
    print(_dict[item])
