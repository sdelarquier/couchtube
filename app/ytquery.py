import dbutils
import json
import nltk
import os
import re


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
            maxResults=5,
            videoEmbeddable='true',
            videoDuration='long',
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
        ep_title, se_number, ep_number, runtime):
        """Finds a youtube video for a given episode
Each video is scored first:
- [0-2]: the show name is in the video name
- [0-1]: the episode title is in the video name
- [0-0.5]: the season number is in the video name
- [0-0.5]: the episode number is in the video name
        """
        # print show_title, ep_title, se_number, ep_number
        lancaster = nltk.LancasterStemmer()
        sh_stem = [lancaster.stem(t) \
            for t in nltk.regexp_tokenize(show_title.encode('utf8'), r"\w+")]

        # Episode stem tokens if exist
        if ep_title:
            ep_stem = [lancaster.stem(t) \
                for t in nltk.regexp_tokenize(ep_title.encode('utf8'), r"\w+")]

        # Build query
        qlist = (show_title, ep_title)
        # Search YouTube
        res = self.search('%s %s' % qlist)

        # Build query
        qlist = (show_title, ep_title, 
            se_number, ep_number)
        # Search YouTube
        res += self.search('%s %s  %s  %s' % qlist)

        # Parse and score results
        vids = []
        for i,v in enumerate(res):
            # Init score
            scores = [0]*4

            # Fix encoding problems
            title = v["snippet"]["title"].encode('utf8')

            # Tokenize and step video title
            tok = nltk.regexp_tokenize(title, r"\w+")
            stem = [lancaster.stem(t) for t in tok]

            # show title in video title
            if len(set(sh_stem) & set(stem)) > 0:
                scores[0] = 1

            # Seson and episode number matching
            season = nltk.regexp_tokenize(title, 
                r"(((?<=[0-9])|\b)[Ss][^0-9\s]*\s*[0-9]{1,2})|([0-9]{1,2}[ \t\r\n\v\f]*x)")
            episode = nltk.regexp_tokenize(title, 
                r"(((?<=[0-9])|\b)[Ee][^0-9\s]*\s*[0-9]{1,2})|(x[ \t\r\n\v\f]*[0-9]{1,2})")
            if season:
                ns = int(nltk.regexp_tokenize(season[0], r"[0-9]{1,2}")[0])
                scores[2] = 0.5 if ns == se_number else 0
            if episode:
                ne = int(nltk.regexp_tokenize(episode[0], r"[0-9]{1,2}")[0])
                scores[3] = 0.5 if ne == ep_number else 0

            # title matching
            if ep_title:
                if season:
                    for s in season:
                        title = title.replace(s, '')
                if episode:
                    for e in episode:
                        title = title.replace(e, '')
                tok = nltk.regexp_tokenize(title, r"\w+")
                stem = [lancaster.stem(t) for t in tok]
                stem = [s for s in stem if s not in sh_stem]
                if stem:
                    scores[1] = len(set(ep_stem) & set(stem))*1./len(set(stem))

            # Total score and append if good enough
            v['score'] = sum(scores)
            # print '======%s: %s (%s): ' % (i, v["snippet"]["title"], v['score'])
            if v['score'] >= 1.55:
                # Get more details about the video
                vid_more = self.video(v['id']['videoId'])[0]
                # Find out if paid content
                v['paid'] = 1 if len(vid_more['contentDetails']['contentRating'])>1 else 0
                if v['paid'] == 1:
                    v['score'] += 10
                # Likes
                v['likes'] = int(vid_more['statistics']['likeCount'].encode('utf8')) - \
                    int(vid_more['statistics']['dislikeCount'].encode('utf8'))
                # Duration
                dur_str = vid_more['contentDetails']['duration'].encode('utf8')
                hr = re.findall('(?<=PT)[0-9]{0,2}(?=H)', dur_str)
                mn = re.findall('(?<=PT)[0-9]{0,2}(?=M)|(?<=H)[0-9]{0,2}(?=M)', dur_str)
                sc = re.findall('(?<=PT)[0-9]{0,2}(?=S)|(?<=M)[0-9]{0,2}(?=S)', dur_str)
                v['duration'] = 0
                v['duration'] += 0 if not hr else 60*int(hr[0])
                v['duration'] += 0 if not mn else int(mn[0])
                v['duration'] += 0 if not sc else int(sc[0])/60.
                if 1. > v['duration']*1./runtime > .5:
                    vids.append(v)
                    # print '====yt: %s / %s (%s) (%s paid)' % (v['duration'], 
                    #     runtime, v['duration']*1./runtime, v['paid'])
                    # print '====yt', vid_more['contentDetails']['contentRating']

        # Return best video if found
        if vids:
            return sorted(vids, 
                key=lambda el: (el['score'], el['likes']))[-1]