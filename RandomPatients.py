from getpass import getpass
import MySQLdb as sql


class RandomSelect(object):

    def __init__(self):
        print("random selection of rows from SQL table")
        self.der_conn = None
        self.der_cur = None
        self.der_table_name = None

    def connect_der_db(self, database, table_name):
        self.der_conn = sql.connect(**database)
        self.der_cur = self.der_conn.cursor()
        self.der_table_name = table_name

    # gets random results and stores in table rands in derived database
    def select_random_rows(self, accesstable, requestedColumns, randNum):
        exec_str = f"DROP PROCEDURE IF EXISTS get_rands;"
        self.der_cur.execute(exec_str) 
        exec_str = f'''
                        CREATE PROCEDURE get_rands(IN cnt INT)
                        BEGIN
                        DROP TABLE IF EXISTS rands;
                        CREATE TABLE rands ( rand_id INT );

                        loop_me: LOOP
                            IF cnt < 1 THEN
                                LEAVE loop_me;
                            END IF;

                            INSERT INTO rands
                            SELECT r1.ROW_ID
                            FROM {accesstable} AS r1 JOIN
                                (SELECT (RAND() *
                                (SELECT MAX(ROW_ID)
                                    FROM {accesstable})) AS id)
                                        AS r2
                                WHERE r1.ROW_ID >= r2.id
                                ORDER BY r1.ROW_ID ASC
                                LIMIT 1;

                            SET cnt = cnt - 1;
                            END LOOP loop_me;
                        END; '''
        self.der_cur.execute(exec_str)
        self.der_conn.commit()
        exec_str = f" CALL get_rands({randNum});"
        self.der_cur.execute(exec_str)
        self.der_conn.commit()

    def create_table(self, created_table_name):
        exec_str = f"DROP TABLE IF EXISTS {created_table_name}"
        self.der_cur.execute(exec_str)
        self.der_conn.commit()
        exec_str = f"""
                    CREATE TABLE {created_table_name}
                    (rand_id int AUTO_INCREMENT NOT NULL, 
                    SUBJECT_ID mediumint UNSIGNED, 
                    PRIMARY KEY (rand_id))"""
        self.der_cur.execute(exec_str)
        self.der_conn.commit()
        exec_str = f"""
                    INSERT INTO 
                        {created_table_name} (SUBJECT_ID) 
                    SELECT 
                        DISTINCT SUBJECT_ID FROM {self.der_table_name}"""
        self.der_cur.execute(exec_str)
        self.der_conn.commit()
        print("Table of SUBJECT_ID ordered by ASC int created")

if __name__ == "__main__":
    print("Starting")
    user = 'root'
    pw = getpass(f'What is the password for the user {user}?\n')

    der_db = {'user': user, 'db': 'derived', 'host': 'db01.healthcreek.org', 'password': pw}

    example = RandomSelect()
    example.connect_der_db(der_db, "patients_as_cui")

    # requested columns should be in form r1.[column], table name should be in form [database].[table]
    # example.select_random_rows('mimic.D_LABITEMS','r1.CUI' , 10)

    example.create_table("patients_as_index")