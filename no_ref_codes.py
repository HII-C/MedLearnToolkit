import numpy as np
import psycopg2
import pymysql
from getpass import getpass
from collections import defaultdict
from sklearn import (ensemble, feature_selection, linear_model, neural_network,
                     svm, tree)
from sklearn.linear_model import LogisticRegression

# NOTE: Look at potientally implementing GridSearchCV in the future
# from sklearn.model_selection import GridSearchCV

class no_umls_codes():
    user_ = input("What is the MySQL user?\n")
    host_ = input("\nWhat is the MySQL host name/location?\n")
    db_ = input("\nWhat is the MySQL Database name?\n")
    password_ = getpass()
    conn = pymysql.connect(user=user_, host=host_ ,db=db_,password=password_)
    cur = conn.cursor()

    def __init__(self, target):
        self.target = target


    # NOTE: Only used as we don't have static code dictionaries (LOINC, SNOMED, etc) loaded to @general right now
    def code_generation(self, mapping_from, query_size, from_index, db_features, flag):
        patient_matrix = {}
        code_dict = {}
        query_string = ("SELECT {0} from {1} ORDER BY RAND() limit {2};").format(db_features, mapping_from, query_size)
        self.cur.execute(query_string)
        rows = self.cur.fetchall()
        visit_matrix = {}
        for row in rows:
            if flag == False:
                query_val = row[from_index]
            else:
                query_val = tuple([row[from_index], row[from_index+1]])
            # row[0] = patient_id, row[1] = visit_id, row[3+] = queries
            if row[0] in visit_matrix:
                patient_matrix[row[0]].append(query_val)
                if row[1] in visit_matrix[row[0]]:
                    if (query_val in code_dict):
                        visit_matrix[row[0]][row[1]].append(query_val)
                    else:
                        if (query_val not in self.target):
                            code_dict[query_val] = query_val
                        visit_matrix[row[0]][row[1]].append([query_val])
                else:
                    visit_matrix[row[0]][row[1]] = [query_val]
            else:
                patient_matrix[row[0]] = [query_val]
                visit_matrix[row[0]] = dict()
                visit_matrix[row[0]][row[1]] = [query_val]
        self.code_dict = code_dict
        self.patient_matrix = patient_matrix
        self.visit_matrix = visit_matrix

    def explosive_code_generation(self, mapping_from, query_size, from_index, db_features):
        patient_matrix = {} #This is a matrix sorted by patients
        visit_matrix = {} #This is a matrix sorted by vists (HADM_ID)
        code_dict = {} #This is the dictionary of certain values, I want it to be populated with values (ex: HADMID: <Value>)
        query_string = ("SELECT {0} from {1} ORDER BY RAND() limit {2};").format(db_features, mapping_from, query_size) #This is the string to prompt the mysql to retrieve certain data
        self.cur.execute(query_string) #executes the string above on to command lin
        rows = self.cur.fetchall() #fetches all the vlaues from the executed query_string statement
        for row in rows: #iterates the row (is the row the whole table?)
            query_val = tuple([row[0], row[1], row[2]]) #(subject_id, hadm_id, item_id)
            if row[0] in visit_matrix: #check if the subject_id which is the patient id is already in the visit matrix or not
                patient_matrix[row[0]].append(query_val) #if so, it adds the the patient id to the patient matrix at key of subject_id
                if row[1] in visit_matrix[row[0]]: #check if the hadm_id which is visit id is present in the visit_matrix at the subject_id key (if the hadm_id is at the patient key)
                    if (query_val in code_dict): #checks if the query_val in code_di
                        visit_matrix[row[0]][row[1]].append(query_val) #appends the query val to the visit matrix at patient
                    else:
                        if (query_val not in self.target):
                            code_dict[query_val] = query_val #adds the value query_val to the code dictionary with the query_val key
                            visit_matrix[row[0]][row[1]].row(query_val) #appends the query_val to the visit matrix at patient at visit
                        else:
                            visit_matrix[row[0]][row[1]] = [query_val] #adds the value query_val to the code visit_matrix dictionary with the patient and then visit id       
                else:
                    patient_matrix[row[0]] = [query_val] #sets the value query_val with the new key patient id
                    visit_matrix[row[0]] = dict() #initializes a 2d matrix
                    visit_matrix[row[0]][row[1]]= [query_val] #sets the value query_val with the new key patient id and then visit id
            #sets the dictionaries to the global scale
        self.code_dict = code_dict
        self.patient_matrix = patient_matrix            
        self.visit_matrix = visit_matrix




    # Generates a sparse attribute matrix based on HADM_ID's, higher resolution than patient, but might to "too much"
    def sparse_matrix_generation_by_visit(self):
        visit_sparse_matrix = dict()

        for patient_id in self.patient_matrix:
            for visit_id in self.visit_matrix[patient_id]:
                visit_sparse_matrix[visit_id] = []
                for code in self.code_dict:
                    if code in self.visit_matrix[patient_id][visit_id]:
                        visit_sparse_matrix[visit_id].append(1)
                    else:
                        visit_sparse_matrix[visit_id].append(0)
        return visit_sparse_matrix

    def sparse_matrix_generation_by_visit_explosion(self):
        visit_explosion_matrix = dict()
        for patient_id in self.patient_matirx:
             for visit_id in self.visit_matrix[patient_id]:
                 visit_explosion_matrix[visit_id] = []
                 for code in self.code_dict:
                     if code in self.visit_matrix[patient_id][visit_id]:
                         #tuple format [high, medium, low]
                         if self.visit_matrix[patient_id][visit_id][2] >= 1:
                             value_tuple = tuple(1,0,0)
                         elif self.visit_matrix[patient_id][visit_id][2] >= 0 and self.visit_matrix[patient_id][visit_id][2] < 1:
                             value_tuple = tuple(0, 1, 0)
                         else:
                             value_tuple = tuple(0, 0, 1)
                             visit_explosion_matrix.append(value_tuple)    
                    else:
                         value_tuple = tuple(0,0,0)                 
                         visit_explosion_matrix.append(value_tuple)
            return visit_explosion_matirx

    # Generates a sparse attribute matrix by subject_id, less resolution but perhaps more "whole" picture
    # NOTE: Both _visit and _patient need to be evalutated to know which is better
    # We should explore creating a standard measure of success once we start training in earnest
    def sparse_matrix_generation_by_patient(self):
        patient_sparse_matrix = dict()
        # print(self.patient_matrix)
        for patient_id in self.patient_matrix:
            patient_sparse_matrix[patient_id] = []
            for code in self.code_dict:
                if code in self.patient_matrix[patient_id]:
                    patient_sparse_matrix[patient_id].append(1)
                else:
                    patient_sparse_matrix[patient_id].append(0)
        return patient_sparse_matrix
    #made by james
    def sparse_martrix_gerenation_exposion_by_pateint(self):
        patient_sparse_matrix = dict()
        for patient_id in self.patient_matrix:
            patient_sparse_matrix[patient_id] = []
            for code in self.code_dict:
                if code in self.patient_matrix[patient_id]:
                    if self.patient_matrix[patient_id] >= 1:
                        tuple_val = tuple(1, 0, 0)
                        
                    elif self.patient_matrix[patient_id] >= 0 and self.patient_matrix[patient_id] < 1:
                        tuple_val = tuple(0, 1, 0)
                        
                    else:
                        tuple_val = tuple(0 ,0 ,1)
                        patient_sparse_matrix[patient_id].append(tuple_val)
                else:
                    tuple_val = tuple(0,0,0)
                    patient_sparse_matrix[patient_id].append(tuple_val)
        return patient_sparse_matrix
    # Creating the data structures needed for any regression/ML @ the visit resolution
    # NOTE: We use contiguious blocks of memory with NumPy, this is crucial for performance
    def array_generation_for_ml_visit(self, mapping_to, visit_matrix, db_features):
        string_tuple = list()
        for x in visit_matrix.keys():
            try:
                if x != None:
                    string_tuple.append(str(x))
            except TypeError as te:
                print(te)
                print(visit_matrix.keys())
                print(x)
        string_tuple = tuple(string_tuple)
        query_string = ("SELECT {0} from {1} WHERE hadm_id in {2}").format(db_features, mapping_to, string_tuple)
        self.cur.execute(query_string)
        target_rows = self.cur.fetchall()
        target_dict = {}
        for item in target_rows:
            if item[1] in target_dict:
                target_dict[item[1]].append(item[2])
            else:
                target_dict[item[1]] = [item[2]]

        X = np.zeros(shape=(len(target_dict.keys()), len(self.code_dict.keys())))
        y = np.zeros(shape=(len(target_dict.keys())))

        count_y = 0
        for item in target_dict:
            X[count_y] = np.array(visit_matrix[item])
            for tar in self.target:
                if (tar in target_dict[item]):
                    y[count_y] = 1
                else:
                    y[count_y] = 0
                    break
            count_y += 1
        return X, y


    # Creating the data structures needed for any regression/ML @ the patient resolution
    # NOTE: We use contiguious blocks of memory with NumPy, this is crucial for performance
    def array_generation_for_ml_patient(self, mapping_to, patient_matrix, db_features):
        string_tuple = tuple([str(x) for x in list(patient_matrix.keys())])
        query_string = ("SELECT {0} from {1} WHERE subject_id in {2}").format(db_features, mapping_to, string_tuple)
        self.cur.execute(query_string)
        target_dict = dict()
        target_rows = self.cur.fetchall()
        # map(lambda x: target_dict[x[0]].append(x[2]), target_rows)
        for item in target_rows:
            # target_dict[item[0]].append(item[2])
            if item[0] in target_dict:
                target_dict[item[0]].append(item[2])
            else:
                target_dict[item[0]] = [item[2]]

        X = np.zeros(shape=(len(target_dict.keys()), len(self.code_dict.keys())))
        y = np.zeros(shape=(len(target_dict.keys())))
        # X = [[0]*len(self.code_dict.keys())]*len(target_dict.keys())
        # y = [0]*len(target_dict.keys())

        for index, item in enumerate(target_dict.keys()):
            X[index] = patient_matrix[item]
            for tar in self.target:
                if (tar in target_dict[item]):
                    y[index] = 1
                elif y[index] != 1:
                    y[index] = 0
        return X, y

    def minimize_ml_attributes(self, X):
        for index, value in X[0]:
            remove_flag = True
            for i in range(0, len(X)):
                if X[i][index] == 1:
                    remove_flag = False
            if remove_flag == True:
                for i in range(0, len(X)):
                    del X[i][index]
        for i in range(0, len(X)):
            X[i] = tuple(X[i])
        X = np.asarray(X)
        return X

    # Logisitic Regression using Lasso optimization and Lars algorithm
    # New, important topics: One-hot encoding
    # http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html
    def learning_by_target_lasso(self, X, y, alpha, input_c=None):
        # alphas = np.logspace(-3, 0, 20)
        print(("Finding the most important half of {} features").format(len(X[0])))
        regr = linear_model.LogisticRegression(penalty="l2", C=input_c, n_jobs=-1, solver="newton-cg")
        rfe = feature_selection.RFE(regr)
        rfe.fit(X, y)
        new_dict = dict()
        for index, code in enumerate(list(self.code_dict)):
            # new_dict[code] = regr.coef_[0][index]
            new_dict[code] = rfe.ranking_[index]
        return new_dict

    # Logisitic Regression using Cross-validation for alphas, hence no fit->score iteration like in lasso
    # def learning_by_target_logisticCV(self, X, y):
    #     regr = linear_model.LogisticRegressionCV()
    #     regr.fit(X,y)
    #     return regr.coef_[0]

    
    # Preserves and orders codes by values, though keys come from scoring matrix, so identical keys 
    # (ex. {1, 0, 0, -1}, 0 is clearly duplicate) will map to 1 value (Condition/Observation code)
    # In all cases I can think of this is inconsequential (non-integer values are floats which)
    # have almost 0 chance of being identical, esp for the crucial in regression which are what we care about.
    def order_output_matrix(self, _list):
        _dict = dict()
        count = 0
        return ((sorted(_list.items(), key=lambda x: x[1]))[::-1], _list)
        #for item in self.code_dict.keys():
        #    _dict[_list[count]] = item
        #    count += 1
        # _list.sort()
        #return(_list, _dict)
