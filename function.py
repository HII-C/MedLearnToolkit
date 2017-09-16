import math
import psycopg2
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn.model_selection import GridSearchCV, KFold
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
    visit_matrix = {}
    visit_count = 0
    for row in rows:
        # row[1] = patient_id, row[2] = visit_id, row[4] = icd_9_code
        if row[1] in patient_matrix.keys():
            if row[2] in patient_matrix[row[1]].keys():
                if (row[4] in code_dict.keys()):
                    patient_matrix[row[1]][row[2]].append(row[4])
                else:
                    code_dict[row[4]] = row[4]
                    patient_matrix[row[1]][row[2]].append([row[4]])
            else:
                patient_matrix[row[1]][row[2]] = [row[4]]
        else:
            patient_matrix[row[1]] = {row[2]: [row[4]]}

    # This loop needs to full set of observations to be formed, must wait to be iterated
    visit_matrix = {}
    visit_count = 0

    for patient_id in patient_matrix.keys():
        for visit_id in patient_matrix[patient_id].keys():
            visit_matrix[visit_id] = []
            for code in code_dict.keys():
                if code in patient_matrix[patient_id][visit_id]:
                    visit_matrix[visit_id].append(1)
                else:
                    visit_matrix[visit_id].append(0)

    string_tuple = list()
    for x in visit_matrix.keys():
        string_tuple.append(int(x))
    string_tuple = tuple(string_tuple)

    query_string = ("SELECT * from mimiciii.DIAGNOSES_ICD WHERE hadm_id in {}").format(string_tuple)
    cur.execute(query_string)
    diagnoses_rows = cur.fetchall()
    diagnoses_dict = {}
    for item in diagnoses_rows:
        if item[2] in diagnoses_dict.keys():
            diagnoses_dict[item[2]].append(item[4])
        else:
            diagnoses_dict[item[2]] = [item[4]]
    X = np.zeros(shape=(len(code_dict.keys()), len(diagnoses_dict.keys())))
    y = np.zeros(shape=(len(diagnoses_dict.keys())))

    count_y = 0
    for item in diagnoses_dict.keys():
        for index, itm in enumerate(visit_matrix[item]):
            X[index][count_y] = itm
        if (diagnoses in diagnoses_dict[item]):
            y[0][count_y] = 1
        else:
            y[0][count_y] = 0
        count_y += 1

    clf = svm.SVC(gamma=.001, C=100)
    clf.fit(X, y)
    print(clf.predict(X[5]))


patientToVector(int('0331'))