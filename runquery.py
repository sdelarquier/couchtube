import dbutils
import datagrab
import ytquery
import pickle
import os


def run_query(title, cache=False):
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

    print '    Merged data'
    # Push show info
    put.put_show(show)
    print '    Pushed show data'
    # Push episode info
    put.put_episodes(show['title'], show['year'], episodes)
    print '    Pushed episodes data'

    # Get YT videos
    yt = ytquery.YtQuery()
    vid_count = 0
    paid_count = 0
    for key, name in episodes.items():
        # print show['title'], name, key[0], key[1], show['runtime']
        vids = yt.get_episode(show['title'], name, 
            key[0], key[1], show['runtime'], debug=True)
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
    # Update show info 
    show['ytcount'] = vid_count
    put.update_show(show['title'], show['year'], 'ytcount', vid_count)
    put.update_show(show['title'], show['year'], 'ytLicensed', paid_count)
    print '    Completed YouTube search and update: %s of %s episodes found' % (vid_count, len(episodes))

    # Close DB access
    put.close()

    return show, episodes