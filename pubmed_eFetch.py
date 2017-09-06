import getpass
import math
import os

import pymysql
import requests
import json
import xmltodict

password = getpass.getpass()
db = pymysql.connect('localhost', 'root', password, 'newschema')
dbCur = db.cursor()

dbCur.execute('SELECT * FROM PREDICATION LIMIT 500')
rows = dbCur.fetchall()

# base_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={}&retmode=json'
# base_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={}&retmode=xml&tool=hiic&email=austinmichne@gmail.com'
post_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/epost.fcgi?db=pubmed&id='
get_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&WebEnv={}&query_key={}&retmode=xml'

for item in rows:
    post_url = post_url + (",{}").format(str(item[2]))

response = requests.post(post_url)
x  = (xmltodict.parse(response.content))

print(x['ePostResult']['WebEnv'])
# print(x['PubmedArticleSet']['PubmedArticle']['MedlineCitation']['MeshHeadingList']['MeshHeading'][5]['DescriptorName']['#text'])
y = requests.get(get_url.format(x['ePostResult']['WebEnv'], x['ePostResult']['QueryKey']))
get_response = (xmltodict.parse(y.content))
# print(get_response['PubmedArticleSet']['PubmedArticle'])
for index, item in enumerate(get_response['PubmedArticleSet']['PubmedArticle']):
    for indx, itm in enumerate(get_response['PubmedArticleSet']['PubmedArticle'][index]['MedlineCitation']['MeshHeadingList']['MeshHeading']):
        print(get_response['PubmedArticleSet']['PubmedArticle'][index]['MedlineCitation']['MeshHeadingList']['MeshHeading'][indx]['DescriptorName']['#text'])
    print('\n')
# print(y)
# print(json.dumps(xmltodict.parse(y.content)))
