import requests
import json
import mysql.connector
from mysql.connector import errorcode
import datetime as dt

class DataGrab(object):
    """Grabs data from IMDB, FreeBase and TheTVDB, 
places in into three identical structures, ready for merging"""
    def __init__(self, show_title):
        self.show_title = show_title
        self.imdb = self.get_imdb()
        self.freb = self.get_freb()
        self.tvdb = self.get_tvdb()

    def get_imdb(self):
        """Get IMDB data through the mymoviedb api
This tends to be a bit flaky (their server drops out everyday)
        """
        imdb_query = {
            "title": "",
            "type": "json",
            "plot": "simple",
            "episode": 1,
            "limit": 1,
            "yg": 0,
            "lang": "en-US",
            "offset": "",
            "aka": "simple",
            "release": "simple"}
        imdb_url = "http://mymovieapi.com/"

