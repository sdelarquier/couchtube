import mysql.connector
from mysql.connector import errorcode
import json
import os


class DbAccess(object):
    """Access database"""
    def __init__(self, db_name, usr, pwd=None):
        self.db_name = db_name
        self.cnx = self.connect(usr, pwd)
        self.cursor = self.cnx.cursor()

    def connect(self, usr, pwd=None):
        """Try to connect to DB
        """
        try:
            cnx = mysql.connector.connect(user=usr, password=pwd)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exists")
            else:
                print(err)
            return
        else:  
            try:
                cnx.database = self.db_name 
                return cnx
            except mysql.connector.Error as err:
                print(err)
                exit(1)

    def close(self):
        """Disconnect from DB
        """
        self.cursor.close()
        self.cnx.close()


class DbGet(DbAccess):
    """Retrieve data from MySQL DB"""
    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), 'scrt.json')) as f:
            usr = json.load(f)['db_read']['usr']
        super(DbGet, self).__init__('couchtube', usr)

    def get_shows(self):
        """Get all shows in DB, sorted by YT #videos found
        """
        query = ("SELECT title, year, poster, episodes, ytcount "
                 "FROM series "
                 "ORDER BY ytcount")
        self.cursor.execute(query)
        return [s for s in self.cursor]

    def get_episodes(show, year):
        """Get all episodes of a given show
        """
        query = ("""
            SELECT title, episode, season, ytId
            FROM episodes 
            WHERE series_title="%s" 
            AND series_year=%s
            ORDER BY season, episode;
                """ % (show, year))
        print query
        return [s for s in self.cursor]


class DbPut(DbAccess):
    """Retrieve data from MySQL DB"""
    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), 'scrt.json')) as f:
            usr = json.load(f)['db_write']['usr']
            pwd = json.load(f)['db_write']['pwd']
        super(DbGet, self).__init__('couchtube', usr, pwd)