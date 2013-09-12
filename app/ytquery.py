import dbutils
import json
import nltk
import os


class YtQuery(object):
    """Search Youtube for episodes of a given show
    """
    def __init__(self):
        import sys
        sys.path.append('ytapi')
        from apiclient.discovery import build

        # Build youtube engine
        with open(os.path.join(os.path.dirname(__file__), 'scrt.json')) as f:
            developer_key = json.load(f)['yt']
        youtube_api_service_name = "youtube"
        youtube_api_version = "v3"
        self.yt_engine = build(youtube_api_service_name, youtube_api_version,
            developerKey=developer_key)

    def search(self, keywords):
        """Search youtube for keywords
        """
        search_response = self.yt_engine.search().list(
            q=keywords,
            part="id,snippet",
            maxResults=10,
            type='video'
        ).execute()
        
        return search_response.get("items", [])

    def video(self, id):
        """Get video info from youtube
        """
        vid_response = self.yt_engine.videos().list(
            part="contentDetails,statistics,status",
            id=id,
            maxResults=1
        ).execute()
        
        return vid_response.get("items", [])

    def get_episode(self, show_title, 
        ep_title, se_number, ep_number):
        """Finds a youtube video for a given episode
        """
        # print show_title, ep_title, se_number, ep_number
        lancaster = nltk.LancasterStemmer()
        sh_stem = [lancaster.stem(t) \
            for t in nltk.regexp_tokenize(show_title, r"\w+")]

        # Build query
        qlist = (show_title, ep_title, se_number, ep_number)
        # query = ' '.join([str(w) for w in qlist if w is not None])
        query = '%s %s season %s episode %s' % qlist

        # Search YouTube
        res = self.search(query)

        # Episode stem tokens if exist
        if ep_title:
            ep_stem = [lancaster.stem(t) \
                for t in nltk.regexp_tokenize(ep_title, r"\w+")]

        # Parse and score results
        vids = []
        for i,v in enumerate(res):
            title = v["snippet"]["title"].encode('utf8')

            # title matching
            if ep_title:
                tok = nltk.regexp_tokenize(title, r"\w+")
                stem = [lancaster.stem(t) for t in tok]
                score = len(set(ep_stem) & set(stem))*0.5/len(set(ep_stem))
                if len(set(sh_stem) & set(stem)) > 0:
                    score += .1
                score *= (len(set(ep_stem)) + len(set(sh_stem)))*1./len(set(stem))
            else:
                score = 0.

            # Seson and episode number matching
            season = nltk.regexp_tokenize(title, 
                r"(((?<=[0-9])|\b)[Ss][^0-9\s]*\s*[0-9]{1,2})|([0-9]{1,2}[ \t\r\n\v\f]*x)")
            episode = nltk.regexp_tokenize(title, 
                r"(((?<=[0-9])|\b)[Ee][^0-9\s]*\s*[0-9]{1,2})|(x[ \t\r\n\v\f]*[0-9]{1,2})")
            if season:
                ns = int(nltk.regexp_tokenize(season[0], r"[0-9]{1,2}")[0])
                s_score = 0.25 if ns == se_number else 0
                score += s_score
            if episode:
                ne = int(nltk.regexp_tokenize(episode[0], r"[0-9]{1,2}")[0])
                e_score = 0.25 if ne == ep_number else 0
                score += e_score

            # Total score and append if good enough
            if score >= 0.4:
                v['score'] = score
                v['rel'] = i
                vid_more = self.video(v['id']['videoId'])
                v['paid'] = 1 if vid_more[0]['status']['license'] is 'youtube' else 0
                v['likes'] = int(vid_more[0]['statistics']['likeCount']) - \
                    int(vid_more[0]['statistics']['dislikeCount'])
                v['duration'] = vid_more[0]['contentDetails']['duration']
                vids.append(v)
                # print '==yt: %s (%s): %s' % (v["snippet"]["title"], v['score'], v['duration'])
        
        # Return best video if found
        if vids:
            return sorted(vids, 
                key=lambda el: (el['score'], el['duration'], 
                                el['likes'], el['rel']))[-1]