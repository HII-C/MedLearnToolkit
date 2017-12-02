import no_ref_codes as nrc
from prettytable import PrettyTable
import inquirer
import os
import sys
import re
sys.path.append(os.path.realpath('.'))
print("\n\n\n")
questions = [
  inquirer.List('size',
                message="Which disease would you like to find relations for?",
                choices=['Congestive Heart Failure', 'Diabetes', "Hypertension", "Obesity"],
            ),]
answers = inquirer.prompt(questions)

code_choices = {"Hypertension": ['4010', '4011', '4019'], "Congestive Heart Failure": ['4280'], "Diabetes": ["25000", "25001", "25002"], "Obesity": ["27800", "27801"]}

demo_list = [{"from": "DIAGNOSES_ICD", "to":"DIAGNOSES_ICD", "db_from": "subject_id, hadm_id, icd9_code", "alpha": .001, "l1":.2, "flag":False,\
                "db_to": "subject_id, hadm_id, icd9_code", "results":["D_ICD_DIAGNOSES", "ICD9_CODE", "LONG_TITLE"],"from_index": 2, "print_index": 0},\
                {"from": "LABEVENTS", "to":"DIAGNOSES_ICD", "db_from": "subject_id, hadm_id, itemid", "alpha": .8, "l1":.1,"flag":True,\
              "db_to": "subject_id, hadm_id, icd9_code", "results":["D_LABITEMS", "ITEMID", "LABEL"], "from_index": 2, "print_index": 0}, \
              {"from": "PRESCRIPTIONS", "to":"DIAGNOSES_ICD", "db_from": "subject_id, hadm_id, DRUG", "alpha": 10,"l1":.06,"flag":False,\
                "db_to": "subject_id, hadm_id, icd9_code", "results":["PRESCRIPTIONS", "DRUG"], "from_index":2, "print_index": 0}]

result_list = {"DIAGNOSES_ICD": ["Diagnoses",list()], \
                "LABEVENTS": ["Lab Tests",list()], \
                "PRESCRIPTIONS": ["Medications",list()]}
print(("Okay, finding relations for {}").format(answers['size']))
for item in demo_list:
    grouping_base = nrc.no_ref_codes(code_choices[answers['size']])
    grouping_base.code_generation(item["from"], 27000, item['from_index'], item['db_from'], item['flag'])
    patient_data = grouping_base.sparse_matrix_generation_by_visit()
    X, y = grouping_base.array_generation_for_ml_visit(item['to'], patient_data, item['db_to'])
    list_out = grouping_base.learning_by_target_lasso(X, y, item['alpha'], item['l1'])
    ordered_list, ordered_dict = grouping_base.order_output_matrix(list_out)

    query_tuple = list()
    for res in ordered_list[0:10]:
        print(res)
        query_tuple.append(str(res[0]))
    if item['from'] != "PRESCRIPTIONS":
        query_string = ("SELECT {3} FROM mimiciii.{0} WHERE {1} in {2} LIMIT 10;"\
                        ).format(item["results"][0], item["results"][1], tuple(query_tuple), item["results"][2])
        grouping_base.cur.execute(query_string)
        query_result = grouping_base.cur.fetchall()
        result_list[item['from']][1] = query_result[::-1]
    else:
        result_list[item['from']][1] = query_tuple
    del grouping_base

keys = list(result_list.keys())
result_table = PrettyTable([result_list[keys[0]][0],\
                            result_list[keys[1]][0],\
                            result_list[keys[2]][0]])
try:
    for index, item in enumerate(result_list[keys[0]][1]):
        result_table.add_row([
            result_list[keys[0]][1][index][demo_list[0]["print_index"]],\
            result_list[keys[1]][1][index][demo_list[1]["print_index"]],\
            result_list[keys[2]][1][index]])
        print("")
except IndexError as ex:
    pass
finally:
    print(result_table)

