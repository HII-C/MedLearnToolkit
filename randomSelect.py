from getpass import getpass
import MySQLdb as sql


class randomSelect(object):

    def __init__(self):
        print("random selection of rows from SQL table")
        self.der_conn = None
        self.der_cur = None

    def connect_der_db(self, database):
        self.der_conn = sql.connect(**database)
        self.der_cur = self.der_conn.cursor()

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


if __name__ == "__main__":
    print("Starting")
    user = 'root'
    pw = getpass(f'What is the password for the user {user}?\n')

    der_db = {'user': user, 'db': 'derived', 'host': 'db01.healthcreek.org', 'password': pw}

    example = randomSelect()
    example.connect_der_db(der_db)

    # requested columns should be in form r1.[column], table name should be in form [database].[table]
    example.select_random_rows('mimic.D_LABITEMS','r1.CUI' , 10)


        
