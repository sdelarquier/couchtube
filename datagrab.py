import requests
import json
import os
import datetime as dt


class DataGrab(object):
    """Grabs data from IMDB, FreeBase and theTVDB, 
places in into three identical structures, ready for merging
    """
    def __init__(self, show_title):
        self.show_title = self.check_title(show_title)
        if not self.show_title:
            print('Unknown show: %s' % show_title)


    def check_title(self, show_title):
        """Find exact match for show title on theTVDB
        """
        self.show_title = show_title
        self.get_tvdb(show_only=True)
        if self.tvdb is not None:
            return self.tvdb['Series']['SeriesName']

    def get(self, src):
        """Wrapper for getting data from source src
        """
        if src == 'imdb':
            self.get_imdb()
        elif src == 'freb':
            self.get_freb()
        elif src == 'tvdb':
            self.get_tvdb()

    def get_imdb(self):
        """Get IMDB data through the mymoviedb api
This tends to be a bit flaky (their server drops out everyday)
        """
        query = {
            "title": self.show_title,
            "type": "json",
            "plot": "simple",
            "episode": 1,
            "limit": 5,
            "yg": 0,
            "lang": "en-US",
            "offset": "",
            "aka": "simple",
            "release": "simple"
            }
        url = "http://mymovieapi.com/"
        # Get query results
        tmp = self.get_from_api(url, params=query)
        self.imdb = None
        if tmp and 'code' in tmp and tmp['code'] == 404:
            return
        if tmp is not None and tmp:
            for res in tmp:
                if self.show_title != res['title']: continue
                if 'episodes' not in res: continue
                self.imdb = {}
                if 'poster' in res and 'imdb' in res['poster']:
                    self.imdb['poster'] = res['poster']['imdb']
                else:
                    self.imdb['poster'] = None
                self.imdb['year'] = res['year']
                self.imdb['rating'] = res['rating']
                self.imdb['Episodes'] = {}
                for ep in res['episodes']:
                    if 'season' not in ep or \
                    'episode' not in ep:
                        continue
                    key = (ep['season'], \
                        ep['episode'])
                    self.imdb['Episodes'][key] = ep
                break

    def get_freb(self):
        """Get Freebase data through the freebase api
        """
        query = [{
            "name": self.show_title,
            "seasons": [{
                "episodes": [{
                  "episode_number": None,
                  "name": None
                    }],
                "season_number": None,
                }],
            "air_date_of_first_episode": None,
            "type": "/tv/tv_program"
            }]
        url = 'https://www.googleapis.com/freebase/v1/mqlread'
        api_key = os.environ['freeb']
        params = {
            'query': json.dumps(query),
            'key': api_key
        }
        # Get query results
        tmp = self.get_from_api(url, params=params)['result']
        if tmp is not None and tmp:
            self.freb = {}
            self.freb['air_date_of_first_episode'] = \
                tmp[0]['air_date_of_first_episode']
            self.freb['Episodes'] = {}
            for se in tmp[0]['seasons']:
                for ep in se['episodes']:
                    key = (se['season_number'], \
                        ep['episode_number'])
                    self.freb['Episodes'][key] = ep
        else:
            self.freb = None

    def get_tvdb(self, show_only=False):
        """Get theTVDB data through the theTVDB api
        """
        query = {
            "seriesname": self.show_title,
            }
        api_key = os.environ['tvdb']
        url = 'http://thetvdb.com/api/GetSeries.php'
        # Get query results
        tmp = self.get_from_api(url, params=query)
        if tmp is not None:
            self.tvdb = {}
            try:
                self.tvdb['Series'] = tmp['Series'][0]
                for res in tmp['Series']:
                    if 'FirstAired' in res:
                        self.tvdb['Series'] = res
                        break
            except KeyError:
                self.tvdb['Series'] = tmp['Series']
        else:
            self.tvdb = None
            return
        # Query episodes (separate)
        if not show_only and self.tvdb is not None:
            url_sec = 'http://thetvdb.com/api/%s/series/%s/all' % (
                api_key, self.tvdb['Series']['seriesid'])
            tmp = self.get_from_api(url_sec)
            if tmp is not None:
                self.tvdb['Series'] = tmp['Series']
                self.tvdb['Episodes'] = {}
                for ep in tmp['Episode']:
                    key = (int(ep['SeasonNumber']), 
                        int(ep['EpisodeNumber']))
                    self.tvdb['Episodes'][key] = ep

    def get_from_api(self, url, params=None):
        """Build request and return results
        """
        import xmltodict

        response = requests.get(url, params=params)
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                return xmltodict.parse(response.text)['Data']


class DataMerge(DataGrab):
    """Merge data from different sources among IMDB, theTVDB and FreeBase.
    """
    def __init__(self, show_title, 
        imdb=True, tvdb=True, freeb=True):
        super(DataMerge, self).__init__(show_title)
        self.loaded = {
            'imdb': imdb,
            'tvdb': tvdb,
            'freb': freeb
        }
        # Grab data
        for src in self.loaded:
            if self.loaded[src]:
                self.get(src)
                if getattr(self, src) is None:
                    self.loaded[src] = False
        # Merge data
        self.merge_show()
        self.merge_episodes()

    def merge_show(self):
        """Merge show information
        """
        # Place holder for show information
        self.show = {'title': self.show_title, 
            'year': None, 
            'episodes': None, 
            'poster': None, 
            'rating': None, 
            'ytcount': None,
            'runtime': None}
        # Merge show info 
        # (all except yt video count and episode number)
        test = lambda src, key: src and self.show[key] is None
        # Start with year
        if test(self.loaded['tvdb'], 'year'):
            try:
                self.show['year'] = dt.datetime.strptime(
                    self.tvdb['Series']['FirstAired'],'%Y-%m-%d').year
            except Exception: 
                pass
        if test(self.loaded['freb'], 'year'):
            try:
                self.show['year'] = dt.datetime.strptime(
                    self.freb['air_date_of_first_episode'],'%Y-%m-%d').year
            except Exception: 
                pass
        if test(self.loaded['imdb'], 'year'):
            try:
                self.show['year'] = self.imdb['year']
            except Exception: 
                pass
        # Then rating (imdb or tvdb only)
        if test(self.loaded['tvdb'], 'rating'):
            try:
                self.show['rating'] = self.tvdb['Series']['Rating']
            except Exception: 
                pass
        if test(self.loaded['imdb'], 'rating'):
            try:
                self.show['rating'] = self.imdb['rating']
            except Exception: 
                pass
        # Then poster (imdb or tvdb only)
        if test(self.loaded['tvdb'], 'poster'):
            try:
                if self.tvdb['Series']['poster'] is not None:
                    url = 'http://thetvdb.com/banners/%s' % \
                        self.tvdb['Series']['poster']
                    # pname = self._dlposter(url)
                    # if pname:
                    #     self.show['poster'] = '/%s' % pname
                    self.show['poster'] = url
            except Exception:
                pass
        if test(self.loaded['imdb'], 'poster'):
            try:
                # pname = self._dlposter(self.imdb['poster'])
                # if pname:
                #     self.show['poster'] = '/%s' % pname
                self.show['poster'] = self.imdb['poster']
            except Exception:
                pass
        # Then runtime (tvdb only)
        if test(self.loaded['tvdb'], 'runtime'):
            try:
                self.show['runtime'] = int(self.tvdb['Series']['Runtime'])
            except Exception: 
                pass

    def merge_episodes(self):
        """Merge episodes
        """
        # Place holder for episode list
        self.episodes = {}
        test = lambda src, key: src and key not in self.episodes
        # Iterate through seasons
        nse = 0
        season_found = True
        while season_found:
            nse += 1
            # Iterate through episodes of season
            nep = 0
            episode_found = True
            while episode_found:
                nep += 1
                key = (nse, nep)
                if test(self.loaded['tvdb'], key):
                    try:
                        self.episodes[key] = self.tvdb['Episodes'][key]['EpisodeName']
                    except Exception: 
                        pass
                if test(self.loaded['freb'], key):
                    try:
                        self.episodes[key] = self.freb['Episodes'][key]['name']
                    except Exception: 
                        pass
                if test(self.loaded['imdb'], key):
                    try:
                        self.episodes[key] = self.imdb['Episodes'][key]['title']
                    except Exception: 
                        pass
                if key not in self.episodes:
                    episode_found = False
                    if nep == 1:
                        season_found = False
        self.show['episodes'] = len(self.episodes)

    def _dlposter(self, url):
        """Downloads and image
        """
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            img = os.path.split(url)[-1]
            fname = os.path.join('static/img/posters', img)
            with open(fname, 'wb') as f:
                for chunk in r.iter_content():
                    f.write(chunk)
            return fname