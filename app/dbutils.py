import mysql.connector
from mysql.connector import errorcode

##
# Connect to DB, return connection object
##
def db_connect(db_name=None):
    try:
        cnx = mysql.connector.connect(user='ct_read')
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exists")
        else:
            print(err)
        return
    else:  
        if db_name is not None:
            try:
                cnx.database = db_name 
            except mysql.connector.Error as err:
                print(err)
                exit(1)
        return cnx

##
# Get top 6 rated series
##
def get_top6():
    cnx = db_connect(db_name='couchtube')
    cursor = cnx.cursor()

    query = ("SELECT title, poster, episodes "
             "FROM series "
             "ORDER BY rating "
             "LIMIT 6;")
    cursor.execute(query)
    data = [s for s in cursor]
    print data
    cursor.close()
    cnx.close()

    return data