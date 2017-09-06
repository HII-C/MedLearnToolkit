import getpass
import math
import os

import pymysql
import requests
import json
import xmltodict

password = getpass.getpass()
db_name = input()
db = pymysql.connect('localhost', 'root', password, db_name)
dbCur = db.cursor()

dbCur.execute(('CREATE TABLE IF NOT EXISTS {} (paper_id text, count integer, mesh_terms text, article_type text)').format('mesh_terms'))
dbCur.execute('SELECT * FROM document_count LIMIT 500')
rows = dbCur.fetchall()
count_dict = dict()

# base_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={}&retmode=json'
# base_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={}&retmode=xml&tool=hiic&email=austinmichne@gmail.com'
post_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/epost.fcgi?db=pubmed&id='
get_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&WebEnv={}&query_key={}&retmode=xml'

for item in rows:
    post_url = post_url + (",{}").format(str(item[0]))
    count_dict[item[0]] = item[1]

response = requests.post(post_url)
x  = (xmltodict.parse(response.content))

print(x['ePostResult']['WebEnv'])
# print(x['PubmedArticleSet']['PubmedArticle']['MedlineCitation']['MeshHeadingList']['MeshHeading'][5]['DescriptorName']['#text'])
y = requests.get(get_url.format(x['ePostResult']['WebEnv'], x['ePostResult']['QueryKey']))
get_response = (xmltodict.parse(y.content))
# print(get_response['PubmedArticleSet']['PubmedArticle'])
query_base = "INSERT into mesh_terms (paper_id, count, mesh_terms, article_type) values(\"{}\", {}, \"{}\", \"{}\")"

for index, item in enumerate(get_response['PubmedArticleSet']['PubmedArticle']):
    article_id = get_response['PubmedArticleSet']['PubmedArticle'][index]['MedlineCitation']['PMID']['#text']
    list_of_mesh = list()
    article_type_list = list()
    try:
        for indx, itm in enumerate(get_response['PubmedArticleSet']['PubmedArticle'][index]['MedlineCitation']['MeshHeadingList']['MeshHeading']):
            print(get_response['PubmedArticleSet']['PubmedArticle'][index]['MedlineCitation']['MeshHeadingList']['MeshHeading'][indx]['DescriptorName']['#text'])
            list_of_mesh.append(get_response['PubmedArticleSet']['PubmedArticle'][index]['MedlineCitation']['MeshHeadingList']['MeshHeading'][indx]['DescriptorName']['#text'])
    except KeyError as ex1:
        print(("No {}\n").format(ex1))

    try:
        for entry, entCount in enumerate(get_response['PubmedArticleSet']['PubmedArticle'][index]['MedlineCitation']['Article']['PublicationTypeList']['PublicationType']):
            article_type_list.append(get_response['PubmedArticleSet']['PubmedArticle'][index]['MedlineCitation']['Article']['PublicationTypeList']['PublicationType'][entry]['#text'])
    except KeyError as ex2:
        article_type_list.append(get_response['PubmedArticleSet']['PubmedArticle'][index]['MedlineCitation']['Article']['PublicationTypeList']['PublicationType']['#text'])
    print('\n')
    article_type_string = (' | '.join(article_type_list)).replace('[', '').replace(']' ,'')
    if (len(list_of_mesh) <= 0):
        dbCur.execute(query_base.format(article_id, count_dict[int(article_id)], 'None', article_type_string))
        db.commit()
    else:
        x_1 = (' | '.join(list_of_mesh)).replace('[', '').replace(']' ,'')
        # query_base = "INSERT into mesh_terms (paper_id, mesh_terms) values(\"{}\", \"{}\")"
        # this_insert = query_base.format(str(article_id), str(list_of_mesh[0]))
        # print(this_insert)
        dbCur.execute(query_base.format(str(article_id), count_dict[int(article_id)], str(x_1), str(article_type_string)))
        db.commit()
# print(y)
# print(json.dumps(xmltodict.parse(y.content)))
