import pymysql
import os
import math
import getpass

password = getpass.getpass()
db = pymysql.connect('localhost', 'root', password, 'newschema')
dbCur = db.cursor()

dbCur.execute(('''CREATE TABLE IF NOT EXISTS {} (paper_id real, count int)''').format('document_count'))
db.commit()

dbCur.execute('SELECT * FROM PREDICATION LIMIT 100')

predication_rows = dbCur.fetchall()
print(predication_rows[0])
exit()

dict_of_id = dict()
for index, item in enumerate(predication_rows):
    if (item[2] in dict_of_id.keys()):
        # dict_of_id[item[2]]['item_array'].append(item)
        dict_of_id[item[2]]['count'] += 1


    else:
        dict_of_id[item[2]] = {'paper_id':[item[2]], 'count': 1}



for item in dict_of_id.keys():
    dbCur.execute(('''INSERT INTO document_count VALUES ({}, {})''').format(item, dict_of_id[item]['count']))
    # print(dict_of_id[item])

db.commit()