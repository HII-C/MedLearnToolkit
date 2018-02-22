import os
import MySQLdb as sql

class SemRep:
    def __init__(self):
        self.cur = None
        self.conn = None
        