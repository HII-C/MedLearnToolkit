import os
from ftplib import FTP
import xmltodict
import getpass
import gzip
import MySQLdb as sql

class PubMed:
    def __init__(self, pubmed_prog=None):
        if pubmed_prog is not None:
            self.pubmed_prog = pubmed_prog
        else:
            self.pubmed_prog = 1
        self.conn = None
        self.cur = None
        self.valid_pub_types = ['D017065', 'D016431', 'D016454']
        self.useful_articles = list()
        if (os.path.isfile("pubmed.prog")):
            with open("pubmed.prog", 'r') as handle:
                self.pubmed_prog = int(handle.readline().strip())
        else:
            with open("pubmed.prog", 'w+') as handle:
                handle.write(f'{self.pubmed_prog}\n')
            print("Pubmed progress set to 1")

    def connect_db(self,  database, table_name, drop=False, schema=None):
        self.conn = sql.connect(**database)
        self.cur = self.conn.cursor()
        if drop:
            print(f"Are you sure you want to drop the table {table_name}?")
            print("ALL DATA WILL BE LOST, THIS IS NOT REVERSABLE")
            user_resp = input("y/n?")
            if user_resp != "y":
                print("Exiting now")
                exit()
            else:
                print("Okay, data being dropped")
        self.table_name = table_name
        if drop and (schema is not None):
            self.schema = schema
            exec_str = f"DROP TABLE IF EXISTS {table_name}"
            self.cur.execute(exec_str)
            exec_str = f"CREATE TABLE {table_name} {schema}"
            self.cur.execute(exec_str)

    def file_from_ftp(self, thread_prog_num):
        server_name = 'ftp.ncbi.nlm.nih.gov'
        dir_ = '/pubmed/baseline/'

        file_num = str(thread_prog_num)
        while len(file_num) < 4:
            file_num = f'0{file_num}'

        filename = f'pubmed18n{file_num}.xml'

        ftp = FTP(server_name)
        ftp.login('anonymous', 'austinmichne@gmail.com')
        ftp.cwd(dir_)
        ftp.retrbinary(f'RETR {filename}.gz', open(filename, 'wb+').write)

        xml_file = gzip.open(filename).read()
        art_dict = xmltodict.parse(xml_file)
        for ele_ in art_dict['PubmedArticleSet']['PubmedArticle']:
            for pub_type in ele_['MedlineCitation']['Article']['PublicationTypeList']['PublicationType']:
                try:
                    if pub_type['@UI'] in self.valid_pub_types:
                        self.useful_articles.append(tuple[ele_['MedlineCitation']['PMID']['#text'], pub_type['@UI']])
                except (TypeError, ValueError, AttributeError, IndexError) as er:
                    pass
        os.remove(f'{filename}')

    def write_to_sql(self, insert_str):
        exec_str = f"INSERT INTO {self.table_name} {insert_str} VALUES({self.useful_articles})"
        self.cur.executemany(exec_str, self.useful_articles)
        self.conn.commit()
        self.useful_articles = []


if __name__ == "__main__":
    example = PubMed()
    pw = getpass.getpass()
    db_param = {'user': 'root', 'db': 'pubmed', 'host': 'db01.healthcreek.org', 'password': pw}
    schema = "(PMID CHAR(12), pubtype CHAR(12))"
    insert_str = "(PMID, pubtype)"
    example.connect_db(db_param, 'derived', drop=False, schema=schema)
    pubmed_prog = 900
    while pubmed_prog < 928:
        example.file_from_ftp(pubmed_prog)
        example.write_to_sql(insert_str=insert_str)
        print(pubmed_prog)
        pubmed_prog += 1

