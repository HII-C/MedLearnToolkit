import math
import psycopg2
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn.model_selection import GridSearchCV, KFold
import numpy as np

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

    test_tuple = list()
    for x in visit_matrix.keys():
        test_tuple.append(int(x))
    test_tuple = tuple(test_tuple)

    query_string = ("SELECT * from mimiciii.DIAGNOSES_ICD WHERE hadm_id in {}").format(test_tuple)
    cur.execute(query_string)
    diagnoses_rows = cur.fetchall()
    diagnoses_matrix = {}
    X = list()
    y = list()
    for item in diagnoses_rows:
        dia = 0
        if (diagnoses == item[4]):
            dia = 1
        X.append(visit_matrix[item[2]])
        y.append(dia)

    fold = KFold(3)
    grid = {'C': [1], 'solver': ['newton-cg']}
    clf = LogisticRegression(penalty='l2', max_iter=10000, tol=.0004)
    gs = GridSearchCV(clf, grid, scoring='roc_auc', cv=fold)
    X = np.array(X)
    X = X.flatten()
    y = np.array(code_dict.keys())


    # searchCV = LogisticRegressionCV(Cs=list(np.power(10.0, np.arange(-10, 10))), penalty='l2'
    #     ,scoring='roc_auc'
    #     ,cv=fold
    #     ,random_state=777
    #     ,max_iter=10000
    #     ,fit_intercept=True
    #     ,solver='newton-cg'
    #     ,tol=10)
    g = gs.fit(X, y)
    print(g.best_score_)


patientToVector(int('0331'))