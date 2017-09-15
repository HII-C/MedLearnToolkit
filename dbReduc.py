import pymysql
import getpass

password = getpass.getpass()
db_name = input()
db = pymysql.connect('localhost', 'root', password, db_name)
dbCur = db.cursor()

dbCur.execute(('''CREATE TABLE IF NOT EXISTS {} (paper_id real, count int)''').format('document_count'))
db.commit()

dbCur.execute('SELECT * FROM PREDICATION LIMIT 10000')

predication_rows = dbCur.fetchall()

dict_of_id = dict()
for index, item in enumerate(predication_rows):
    if (item[2] in dict_of_id.keys()):
        # dict_of_id[item[2]]['item_array'].append(item)
        dict_of_id[item[2]]['count'] += 1

    else:
        dict_of_id[item[2]] = {'paper_id': [item[2]], 'count': 1}

for item in dict_of_id.keys():
    dbCur.execute(('''INSERT INTO document_count VALUES ({}, {})''').format(item, dict_of_id[item]['count']))

db.commit()
