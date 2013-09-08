import sys
sys.path.append('ytapi')
from apiclient.discovery import build
import dbutils
import json
import nltk
import os

with open(os.path.join(os.path.dirname(__file__), 'scrt.json')) as f:
    DEVELOPER_KEY = json.load(f)['yt']
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def find_videos_list(keywords):
    # Set DEVELOPER_KEY to the "API key" value from the "Access" tab of the
    # Google APIs Console http://code.google.com/apis/console#access

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
        developerKey=DEVELOPER_KEY)

    search_response = youtube.search().list(
        q=keywords,
        part="id,snippet",
        maxResults=10
        ).execute()
    
    return search_response.get("items", [])


def find_episodes(show, episodes):
    """Try to find a video for each episode
    """
    thumbs = []
    for ep in episodes:
        vid = find_episode(show, *ep)
        if vid:
            print vid["snippet"]["title"]
            thumbs.append((vid['snippet']['thumbnails']['default']['url'],
                vid['snippet']['title']))
        else:
            print None
            thumbs.append(("static/img/thmb_def.png",
                "not found"))

    return thumbs


def find_episode(show, ep_title, ep_ne, ep_ns):
    """Finds a youtube video for a given episode
    """
    lancaster = nltk.LancasterStemmer()
    sh_stem = [lancaster.stem(t) \
            for t in nltk.regexp_tokenize(show, r"\w+")]

    print ep_title, ep_ns, ep_ne

    # Build query
    qlist = [ep_title, ep_ns, ep_ne]
    query = ' '.join([str(w) for w in qlist if w is not None])

    # Search YouTube
    res = find_videos_list(query)

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
            if set(sh_stem) & set(ep_stem):
                score += .1
        else:
            score = 0.

        # Seson and episode number matching
        season = nltk.regexp_tokenize(title, r"(\b[Ss])(.[^0-9]*)([0-9]{1,2})")
        episode = nltk.regexp_tokenize(title, r"(\b[Ee])(.[^0-9]*)([0-9]{1,2})")
        if season:
            ns = int(nltk.regexp_tokenize(season[0], r"[0-9]{1,2}")[0])
            s_score = 0.25 if ns == ep_ns else 0
            score += s_score
        if episode:
            ne = int(nltk.regexp_tokenize(episode[0], r"[0-9]{1,2}")[0])
            e_score = 0.25 if ne == ep_ne else 0
            score += e_score

        # Total score and append if good enough
        if score > 0.45:
            v['score'] = score
            v['rel'] = i
            vids.append(v)
    
    # Return best video if found
    if vids:
        return sorted(vids, key=lambda el: (el['score'], el['rel']))[-1]

def check_title(show_title):
    """Check if the show title entered by user matches either a DB entry, 
or has to be added to the DB.
    """

