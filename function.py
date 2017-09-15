import math
import psycopg2

def patientToVector():
    patient_matrix = {}
    conn = psycopg2.connect("dbname='mimic' user='student' host='localhost' schema='mimiciii'")
    cur = conn.cursor()
    cur.execute("SELECT * from mimiciii.DIAGNOSES_ICD limit 100;")
    rows = cur.fetchall()
    for row in rows:
        if row[1] in patient_matrix.keys():
            if row[2] in patient_matrix[row[1]].keys():
                patient_matrix[row[1]][row[2]].append(row[4])
            else:
                patient_matrix[row[1]][row[2]] = [row[4]]
        else:
            patient_matrix[row[1]] = {row[2]: [row[4]]}
    print(patient_matrix)



# def queryToLabels():


# def learnRanking():


# def returnSuggestions():

