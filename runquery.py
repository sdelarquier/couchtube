import dbutils
import datagrab
import ytquery
import pickle
import os


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

    if debug:
        print '    Merged data'
    yield 'data: %s\n\n' % (3./(count_max+9)*100)
    # Push show info
    put.put_show(show)
    if debug:
        print '    Pushed show data'
    yield 'data: %s\n\n' % (6./(count_max+9)*100)
    # Push episode info
    put.put_episodes(show['title'], show['year'], episodes)
    if debug:
        print '    Pushed episodes data'
    yield 'data: %s\n\n' % (9./(count_max+9)*100)

    # Get YT videos
    yt = ytquery.YtQuery()
    vid_count = 0
    paid_count = 0
    count = 0
    count_max = len(episodes)
    for key, name in episodes.items():
        count += 1
        vids = yt.get_episode(show['title'], name, 
            key[0], key[1], show['runtime'], debug=debug)
        if vids:
            # Update episode info
            vid_count += 1
            paid_count += vids['paid']
            put.update_episode(show['title'], show['year'], key[0], key[1], 
                'ytId', vids['id']['videoId'])
            put.update_episode(show['title'], show['year'], key[0], key[1], 
                'thumb', vids['snippet']['thumbnails']['default']['url'])
            put.update_episode(show['title'], show['year'], key[0], key[1], 
                'paid', vids['paid'])
        yield 'data: %s\n\n' % ((count+9.)*1./(count_max+9)*100)
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
        show['title'], show['year'], count_max, vid_count, paid_count)

