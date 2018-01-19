import math
import psycopg2
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn.model_selection import GridSearchCV, KFold
from sklearn import linear_model
from sklearn import svm
import numpy as np
import scipy

def patientToVector(diagnoses):
    patient_matrix = {}
    code_dict = {}
    conn = psycopg2.connect("dbname='mimic' user='student' host='localhost' password='password'")
    cur = conn.cursor()
    cur.execute("SELECT * from mimiciii.PROCEDURES_ICD limit 10000;")
    rows = cur.fetchall()

    visit_count = 0
    patient_code = dict()
    for row in rows:
        # row[1] = patient_id, row[2] = visit_id, row[4] = icd_9_code
        if row[1] in patient_matrix.keys():
            if (row[4] in code_dict.keys()):
                patient_matrix[row[1]].append(row[4])
            else:
                code_dict[row[4]] = row[4]
                patient_matrix[row[1]].append(row[4])
        else:
            patient_matrix[row[1]] = [row[4]]
            patient_code[row[1]] = []
    # This loop needs to full set of observations to be formed, must wait to be iterated
    for patient_id in patient_matrix.keys():
        for code in code_dict.keys():
            if code in patient_matrix[patient_id]:
                patient_code[patient_id].append(1)
            else:
                patient_code[patient_id].append(0)

    string_tuple = list()
    for x in patient_code.keys():
        string_tuple.append(int(x))
    string_tuple = tuple(string_tuple)

    query_string = ("SELECT * from mimiciii.DIAGNOSES_ICD WHERE subject_id in {}").format(string_tuple)
    cur.execute(query_string)
    diagnoses_rows = cur.fetchall()
    diagnoses_dict = {}
    for item in diagnoses_rows:
        if item[1] in diagnoses_dict.keys():
            diagnoses_dict[item[1]].append(item[4])
        else:
            diagnoses_dict[item[1]] = [item[4]]

    X = np.zeros(shape=(len(patient_code.keys()), len(code_dict.keys())))
    y = np.zeros(shape=(len(patient_code.keys())))

    count_y = 0
    imp_index = 0

    for item in patient_code.keys():
        X[count_y] = np.array(patient_code[item])
        if (diagnoses in diagnoses_dict[item]):
            y[count_y] = 1
        else:
            y[count_y] = 0

        count_y += 1

    regr = linear_model.LogisticRegressionCV()
    regr.fit(X, y)
    print(regr.coef_)
    # scores = [regr.set_params(alpha=alpha).fit(X, y).score(X, y) for alpha in alphas]    
    # best_alpha = alphas[scores.index(max(scores))]
    # regr.alpha = best_alpha
    # query_string = ("SELECT * from mimiciii.DIAGNOSES_ICD WHERE icd9_code = \'{}\' limit 10000;").format(diagnoses)
    # cur.execute(query_string)
    # prediction_rows = cur.fetchall()

    # for row in prediction_rows:
    #     if (row[1] not in patient_code.keys()):
    #         cur.execute(("SELECT * from mimiciii.PROCEDURES_ICD WHERE subject_id = \'{}\';").format(row[1]))
    #         rows = cur.fetchall()
    #         this_patient = list()
    #         for r in rows:
    #             this_patient.append(r[4])

    #         for r in rows:
    #             vis_arr = []
    #             for code in code_dict.keys():
    #                 if code in this_patient:
    #                     vis_arr.append(1)
    #                 else:
    #                     vis_arr.append(0)
    #         print('Should only show once') 
    #         print(regr.predict(np.array(vis_arr).reshape(1, -1)))
    #         exit()
    # print(clf.predict(X[(imp_index):(imp_index + 1)]))


patientToVector('41401')
