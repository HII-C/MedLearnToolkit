import math
import psycopg2

def patientToVector():
    patient_matrix = {}
    code_dict = {}
    code_count = 0
    conn = psycopg2.connect("dbname='mimic' user='student' host='localhost' password='password'")
    cur = conn.cursor()
    cur.execute("SELECT * from mimiciii.DIAGNOSES_ICD limit 100;")
    rows = cur.fetchall()
    for row in rows:
        # row[1] = patient_id, row[2] = visit_id, row[4] = icd_9_code
        if row[1] in patient_matrix.keys():
            if row[2] in patient_matrix[row[1]].keys():
                if (row[4] in code_dict.keys()):
                    patient_matrix[row[1]][row[2]].append(code_dict[row[4]])
                else:
                    code_count += 1
                    code_dict[row[4]] = code_count
                    patient_matrix[row[1]][row[2]].append(code_dict[row[4]])
            else:
                patient_matrix[row[1]][row[2]] = [row[4]]
        else:
            patient_matrix[row[1]] = {row[2]: [row[4]]}
    print(patient_matrix)

patientToVector()

# def queryToLabels():


# def learnRanking():


# def returnSuggestions():

