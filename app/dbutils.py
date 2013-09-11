import mysql.connector
from mysql.connector import errorcode
import json
import os
import nltk


class DbAccess(object):
    """Access database
    """
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
        query = ("""
            SELECT title, year, poster, episodes, ytcount, 
                (episodes - ytLicensed)/episodes*100 as ppay, 
                ytcount/episodes as ytrep
            FROM series
            ORDER BY ytrep DESC
                 """)
        self.cursor.execute(query)
        return [s for s in self.cursor]

    def get_episodes(self, show, year):
        """Get all episodes of a given show
        """
        query = ("""
            SELECT title, season, episode, ytId, thumb
            FROM episodes 
            WHERE series_title=%s
                AND series_year=%s
            ORDER BY season, episode
            """)
        self.cursor.execute(query, (show, year))
        return [s for s in self.cursor]

    def check_title(self, show_title):
        """Check if a show is in the database, allowing for messy entries
        """
        lancaster = nltk.LancasterStemmer()
        show_title_stem = [lancaster.stem(t) \
            for t in nltk.regexp_tokenize(show_title, r"\w+")]
        show_title_reg = ''
        for w in show_title_stem:
            show_title_reg += '%s%% ' % w
        query = ("""
            SELECT title
            FROM series
            WHERE TRIM(LOWER(title)) LIKE %s
            LIMIT 1
            """)
        self.cursor.execute(query, (show_title_reg.strip()))
        data = self.cursor.fetchall()
        if self.cursor.rowcount > 0:
            return data[0]
        else:
            return


class DbPut(DbAccess):
    """Retrieve data from MySQL DB
    """
    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), 'scrt.json')) as f:
            dat = json.load(f)
            usr = dat['db_write']['usr']
            pwd = dat['db_write']['pwd']
        super(DbPut, self).__init__('couchtube', usr, pwd)

    def put_show(self, show):
        """Add a show to the series table
        """
        query = ("INSERT INTO series "
               " (title, episodes, poster, rating, year) "
               " VALUES (%s, %s, %s, %s, %s) "
               " ON DUPLICATE KEY UPDATE "
               "   title=VALUES(title), "
               "   episodes=VALUES(episodes), "
               "   rating=VALUES(rating), "
               "   poster=VALUES(poster), "
               "   year=VALUES(year) ")
        params = (
            show['title'], 
            show['episodes'], 
            show['poster'], 
            show['rating'], 
            show["year"])
        self.cursor.execute(query, params)
        self.cnx.commit()

    def put_episodes(self, show, year, episodes):
        """Add a show to the series table
        """
        query = ("INSERT INTO episodes "
               " (series_title, series_year, season, episode, title) "
               " VALUES (%s, %s, %s, %s, %s) "
               " ON DUPLICATE KEY UPDATE "
               "   series_title=VALUES(series_title), "
               "   series_year=VALUES(series_year), "
               "   episode=VALUES(episode), "
               "   season=VALUES(season), "
               "   title=VALUES(title) ")
        params = [
            (show, year, 
            key[0], key[1], 
            name) for key, name in episodes.items()]
        self.cursor.executemany(query, params)
        self.cnx.commit()

    def update_show(self, show, year, field, value):
        """Update series table with field value
        """
        query = ("""
            UPDATE series
            SET {}=%s
            WHERE title=%s AND year=%s;
            """.format(field))
        params = (value, show, year)
        self.cursor.execute(query, params)
        self.cnx.commit()

    def update_episode(self, show, year, 
        se_number, ep_number, field, value):
        """Update episodes table with field value
        """
        query = ("""
            UPDATE episodes
            SET {}=%s
            WHERE series_title=%s AND series_year=%s
                AND episode=%s AND season=%s;
            """.format(field))
        params = (value, show, year, 
            ep_number, se_number)
        self.cursor.execute(query, params)
        self.cnx.commit()
