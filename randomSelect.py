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
        exec_str = f'''
                        DELIMITER $$
                        DROP PROCEDURE IF EXISTS get_rands$$
                        CREATE PROCEDURE get_rands(IN cnt INT)
                        BEGIN
                        DROP TEMPORARY TABLE IF EXISTS rands;
                        CREATE TEMPORARY TABLE rands ( rand_id INT );

                        loop_me: LOOP
                            IF cnt < 1 THEN
                                LEAVE loop_me;
                            END IF;

                            INSERT INTO rands
                            SELECT {requestedColumns}
                            FROM {accesstable} AS r1 JOIN
                                (SELECT (RAND() *
                                (SELECT MAX(id)
                                    FROM {accesstable})) AS id)
                                        AS r2
                                WHERE r1.id >= r2.id
                                ORDER BY r1.id ASC
                                LIMIT 1;

                            SET cnt = cnt - 1;
                            END LOOP loop_me;
                        END$$
                        DELIMITER ;
                        
                        CALL get_rands({randNum});
        
                 '''
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
    example.select_random_rows("","" , 10)


        
