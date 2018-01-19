from ml_methods import ml_methods
from no_ref_codes import no_umls_codes

diabetes_ml_props = {\
            "from": "DIAGNOSES_ICD",\
            "to":"DIAGNOSES_ICD", \
            "db_from": "subject_id, hadm_id, icd9_code",\
            "c": .483293023857,\
            "l1":.2,\
            "flag":False,\
            "db_to": "subject_id, hadm_id, icd9_code",\
            "results":["D_ICD_DIAGNOSES", "ICD9_CODE", "LONG_TITLE"],\
            "from_index": 2,\
            "print_index": 0\
            }

diabetes_codes = ["25000", "25001", "25002"]
testing_ml = no_umls_codes(diabetes_codes)
testing_ml.code_generation(diabetes_ml_props["from"],\
                              5000,\
                              diabetes_ml_props['from_index'],\
                              diabetes_ml_props['db_from'],\
                              diabetes_ml_props['flag'])

patient_data = testing_ml.sparse_matrix_generation_by_patient()
X, y = testing_ml.array_generation_for_ml_patient(diabetes_ml_props['to'],\
                                                     patient_data,\
                                                     diabetes_ml_props['db_to'])

classifier = ml_methods()
ordered_list = classifier.MLP(X, y)

query_tuple = list()
for res in ordered_list[0:10]:
    # print(res)
    query_tuple.append(str(res[0]))

query_string = ("SELECT {3} FROM {0} WHERE {1} in {2} LIMIT 10;").format\
                (diabetes_ml_props["results"][0],\
                 diabetes_ml_props["results"][1],\
                 tuple(query_tuple),\
                 diabetes_ml_props["results"][2])
testing_ml.cur.execute(query_string)
query_result = testing_ml.cur.fetchall()
print(query_result[::-1])
