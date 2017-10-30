import pymysql

class derived_layer_creation(object):

    def __init__(self):
        print("Derived layer process started")


    def create_database(self, host_, user_, password_, name_, delete_):
        self.connection = pymysql.connect(host=host_, user=user_, password=password_)
        self.cursor = self.connection.cursor()
        if (delete_ == True):
            print("Are you sure that you want to remove any existing derived database? y/n")
            user_check = input()
            if (user_check == "y"):
                try:
                    exec_str = ("DROP DATABASE IF EXISTS {};").format(name_)
                    self.cursor.execute(exec_str)
                    exec_str = ("CREATE DATABASE {};").format(name_)
                    self.cursor.execute(exec_str)
                    print("Database successfuly removed/created")
                except Exception as ex:
                    print("Unable to drop with exception:", ex)
            else:
                try:
                    self.cursor.execute(("CREATE DATABASE {};").format(name_))
                    print(("Database {} created").format(name_))
                except Exception as ex:
                    print("There was an exception, this database may already exist \n", ex)
                    print("Would you like to exit? y/n")
                    resp = input()
                    if (resp == "y"):
                        exit()

    def create_term_table(self, derived_db_name, umls_db):
        try:
            creation_str = ("create table {}.term (tid MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT, str VARCHAR(500), PRIMARY KEY(tid)) ENGINE = MYISAM;").format(derived_db_name)
            self.cursor.execute(creation_str)
            try:
                insertion_str = ("insert into {}.term(str) select DISTINCT STR from {}.MRCONSO;").format(derived_db_name, umls_db)
                self.cursor.execute(insertion_str)
            except Exception as ex:
                print("SQL Error with insertion on table TERM, see attached error code:\n", ex)
                self.connection.commit()
        except Exception as ex:
            print("Term table creation failed, table might already exist, or other error. \n", ex)
        self.connection.commit()
        # Creating the greedy algorithm basis for NLP DB
        # select distinct str from UMLS.MRCONSO_NLP order by frequency desc;


    def create_concept_table(self, derived_db_name, umls_db):
        try:
            creation_str = ("create table {}.concept (cid MEDIUM UNSIGNED NOT NULL AUTO_INCREMENT, cui CHAR(8) UNIQUE, str VARCHAR(500), PRIMARY KEY(cid)) ENGINE = MYISAM;").format(derived_db_name)
            self.cursor.execute(creation_str)
            try:
                insertion_str = ('insert into {0}.concept(cui, str) select DISTINCT CUI, STR from {1}.MRCONSO WHERE STT = "PF" AND TS = "P" AND ISPREF = "Y" AND LAT = "ENG";').format(derived_db_name, umls_db)
                self.cursor.execute(insertion_str)
            except Exception as ex:
                print("SQL Error with insertion on table CONCEPT, see attached error code:\n", ex)
                self.connection.commit()
        except Exception as ex:
            print("Concept table creation failed, table might already exist, or other error. \n", ex)


    def create_term_to_concept(self, derived_db_name, umls_db, term_table_name, concept_table_name):
        try:
            creation_str = ("create table {}.term2concept (tid MEDIUMINT UNSIGNED NOT NULL, cid UNSIGNED SMALLINT NOT NULL, key(tid), key(cid));").format(derived_db_name)
            self.cursor.execute(creation_str)
            try:
                insertion_str = ("insert into {0}.term2concept select {0}.{2}.tid, {0}.{3}.cid from {1}.MRCONSO, term t, concept c where cui = {0}.{2}.cid and str = {0}.{3}.str;").format(derived_db_name, umls_db, term_table_name, concept_table_name)
                self.cursor.execute(insertion_str)
            except Exception as ex:
                print("SQL Error with insertion, see attached error code:\n", ex)
                self.connection.commit()
        except Exception as ex:
            print("Table creation failed, table might already exist, or other error. \n", ex)
        self.connection.commit()


if __name__ == "__main__":
    test_layer = derived_layer_creation()
    test_layer.create_database("localhost", "root", "password", "der", True)
    # test_layer.create_term_table("der", "UMLS")
    print("Term done")
    test_layer.create_concept_table("der", "UMLS")
    print("Done")
    
# select AUI, CUI from UMLS.MRCONSO
# into outfile -- blah some lookup (dict) file

# select CUI, AUI, SAB, PTR from UMLS.MRHIER
# where RELA = "isa"
# into outfile -- blah some text file
# ;

# python the heck out of it
# loop over file line by line
# set AUI1
# from right to left PTR
   # get AUI2
   # output getCUI(AUI1) isa SAB getCUI(AUI2)
   # set AUI1, AUI2, repeat

# get distinct lines
# output to text file

# create table hier(
#   sab,
#   cid1,
#   cid2,
#   unique(sab, cui1, cui2)
# )

# load data infile --  from that file

# create table rel(
#   sab,
#   cid1,
#   rela,
#   cid2
# )
  
#   insert into rel select CUI2, CUI1, RELA, SAB from UMLS.MRREL;