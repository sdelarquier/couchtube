import dbutils
import datagrab
import ytquery
import pickle
import os
import sys


def run_query(title, cache=False, debug=False):
    """Execute all steps of an actual query, from getting/merging data, to placing it in the DB
    """
    # Open Push access to DB
    put = dbutils.DbPut()

    # Get merged data 
    if cache and os.path.exists('merged.%s.dat' % title):
        with open('merged.%s.dat' % title, 'rb') as f:
            show = pickle.load(f)
            episodes = pickle.load(f)
    else:
        merged = datagrab.DataMerge(title)
        if cache:
            with open('merged.%s.dat' % title, 'wb') as f:
                pickle.dump(merged.show, f)
                pickle.dump(merged.episodes, f)
        show = merged.show
        episodes = merged.episodes

    # number of episodes
    count_max = len(episodes)

    if debug:
        print '    Merged data'
    yield 'data: %s\n\n' % (2./(count_max+6)*100)
    # Push show info
    put.put_show(show)
    if debug:
        print '    Pushed show data'
    yield 'data: %s\n\n' % (4./(count_max+6)*100)
    # Push episode info
    put.put_episodes(show['title'], show['year'], episodes)
    if debug:
        print '    Pushed episodes data'
    yield 'data: %s\n\n' % (6./(count_max+6)*100)

    # Get YT videos
    yt = ytquery.YtQuery()
    # empty counters
    count = 0
    vid_count = 0
    paid_count = 0
    # Threaded episode search and match
    for key, name in episodes.items():
        query_res = yt.query_episode(
            show['title'], name, 
            key[0], key[1], show['runtime'])
        count += 0.5
        yield 'data: %s\n\n' % ((count+6.)*1./(count_max+6.)*100)
        vids = yt.get_episode(query_res, debug=debug)
        
        count += 0.5
        if vids:
            # Update episode info
            vid_count += 1
            paid_count += vids['paid']
            put.update_episode(show['title'], show['year'], 
                key[0], key[1], 
                'ytId', vids['id'])
            put.update_episode(show['title'], show['year'], 
                key[0], key[1], 
                'thumb', vids['snippet']['thumbnails']['default']['url'])
            put.update_episode(show['title'], show['year'], 
                key[0], key[1], 
                'paid', vids['paid'])
        yield 'data: %s\n\n' % ((count+6.)*1./(count_max+6.)*100)

    # Update show info 
    show['ytcount'] = vid_count
    put.update_show(show['title'], show['year'], 'ytcount', vid_count)
    put.update_show(show['title'], show['year'], 'ytLicensed', paid_count)
    if debug:
        print '    Completed YouTube search and update: %s of %s episodes found' % (
            vid_count, count_max)

    # Close DB access
    put.close()

    # return show, episodes
    yield 'event: end\ndata: %s\ndata: %s\ndata: %s\ndata: %s\ndata: %s\n\n' % (
        show['title'], show['year'], count_max, vid_count, vid_count-paid_count)


def run_all(cache=False, debug=False):
    """Updates all series from the database
    """
    db = dbutils.DbGet()
    series = db.get_shows()
    db.close()
    pwd = os.path.abspath(os.path.curdir)
    for title in series:
        print title[0]
        run = run_query(title[0], cache=True, debug=False)
        for it in run:
            print it


if __name__ == "__main__":
    if len(sys.argv) == 1:
        run_all(cache=True, debug=False)
    elif len(sys.argv) == 2:
        title = sys.argv[1]
        run = run_query(title, cache=True, debug=False)
        for it in run:
            print it

