import no_ref_codes as nrc

grouping_base = nrc.no_ref_codes('4280')
grouping_base.code_generation(20000)
patient_data = grouping_base.sparse_matrix_generation_by_patient()
X, y = grouping_base.array_generation_for_ml_patient(patient_data)
list_out = grouping_base.learning_by_diagnoses_lasso(X, y)
ordered_list, ordered_dict = grouping_base.order_output_matrix(list_out)

query_tuple = list()
for item in ordered_list[0:15]:
    query_tuple.append(ordered_dict[item])
    
query_tuple = tuple(query_tuple)
query_string = ("SELECT * FROM mimiciii.D_LABITEMS WHERE ITEMID in {};").format(query_tuple)
grouping_base.cur.execute(query_string)
query_result = grouping_base.cur.fetchall()

for item in query_result:
    print(item[2], item[5], item[4])
