from sklearn.linear_model import LogisticRegression;
from sklearn.cluster import KMeans
import jenkspy as jnk
import numpy as np
import pymysql

class ValueRangeDetermination(object):
    def __init__(self):
        print("")
        self.connection = None
        self.cursor = None
        self.table = None
        self.observations = None

    def connect_db(self, database):
        host_ = database["host"]
        user_ = database["user"]
        password_ = database["password"]
        self.connection = pymysql.connect(host=host_, user=user_, password=password_)
        self.cursor = self.connection.cursor()

    def fetch_observation(self, observation, n_to_fetch):
        if (self.connection or self.connection) == None:
            raise ConnectionError

        query_str = ("SELECT {} from {} WHERE ITEMID = {} LIMIT {}").format(observation, self.table,
                                                                                 observation, n_to_fetch)

        self.cursor.execute(query_str)
        temp_obs = self.cursor.fetchall()

        ## value, flag, valueuom
        # 2 right now, can change
        # for index, value in enumerate(temp_obs):
        #     temp_obs[index][1] =
        temp_np_arr = np.asarray(temp_obs)
        self.observations = temp_np_arr

    def kmeans_grouping(self):
        kmeans = KMeans(n_clusters=3, random_state=0)
        # log_r = LogisticRegression()
        # log_r.fit(X=self.observations[0], y=self.observations[1])
        kmeans.fit(self.observations[0])

    def jenks_nat_breaks(self):
        jenk = jnk.jenks_breaks(self.observations[0], 3)
        print(jenk)



if __name__ == "__main__":
    db = {"user": "hiic", "password": "greenes2018", "host": "db01.healthcreek.org"}
    vrd_test = value_range_det()
    vrd_test.table = "mimic.LABEVENTS"
    vrd_test.connect_db(db)
    vrd_test.fetch_observation("50931", 1000)
    vrd_test.jenks_nat_breaks()