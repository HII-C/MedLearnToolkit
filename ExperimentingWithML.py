from MachineLearningMethods import MachineLearningMethods as MchLrnMeth
from NoUmlsCodes import NoUmlsCodes as NoUC
import heapq
import numpy as np

diabetes_ml_props = {\
            "to": "DIAGNOSES_ICD",\
            "from":"LABEVENTS", \
            "db_to": "subject_id, hadm_id, icd9_code",\
            "c": .483293023857,\
            "l1":.2,\
            "flag":False,\
            "db_from": "subject_id, hadm_id, ITEMID",\
            "results":["D_LABITEMS", "ITEMID", "LABEL"],\
            "from_index": 2,\
            "print_index": 0\
            }

diabetes_codes = ["25000", "25001", "25002"]
testing_ml = NoUC(diabetes_codes)
testing_ml.code_generation(diabetes_ml_props["from"],\
                              50,\
                              diabetes_ml_props['from_index'],\
                              diabetes_ml_props['db_from'],\
                              diabetes_ml_props['flag'])

patient_data = testing_ml.sparse_matrix_generation_by_patient()
X, y = testing_ml.array_generation_for_ml_patient(diabetes_ml_props['to'],\
                                                     patient_data,\
                                                     diabetes_ml_props['db_to'])

classifier = MchLrnMeth()
ordered_list = classifier.linear_regr(X, y)

code_list = list(testing_ml.code_dict.keys())
float_to_code_dict = dict()
same_float_fixer = 0

for i in range(0, len(ordered_list)):
    temp_val = ordered_list[i]
    while temp_val in float_to_code_dict:
        temp_val += .0001 / (2**same_float_fixer)
        same_float_fixer += 1
    float_to_code_dict[temp_val] = code_list[i]

largest_vals = heapq.nlargest(10, list(float_to_code_dict.keys()))
vals_to_codes = list(map(lambda x: float_to_code_dict[x], largest_vals))
query_tuple = tuple(map(lambda x: int(x), vals_to_codes))
print(largest_vals)
print(vals_to_codes)
print(query_tuple)

query_string = ("SELECT ({3}) FROM {0} WHERE {1} in {2} LIMIT 10;").format\
                (diabetes_ml_props["results"][0],\
                 diabetes_ml_props["results"][1],\
                 query_tuple,\
                 diabetes_ml_props["results"][2])
testing_ml.cur.execute(query_string)
query_result = testing_ml.cur.fetchall()
print(query_result[::-1])
