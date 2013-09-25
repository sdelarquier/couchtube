import dbutils
import datagrab
import ytquery
import pickle
import os
import sys
import threading
import Queue


# Create threading lock
GRID_LOCK = threading.Lock()
# empty counters
count = 0
vid_count = 0
paid_count = 0


class EpisodeQuery(threading.Thread):
    """Unique thread for single episode video search and match
    """
    def __init__(self, key, name, yt, 
    show, count_max, queue, put, 
    debug=True):
        super(EpisodeQuery, self).__init__()
        self.key = key
        self.name = name
        self.yt = yt
        self.show = show
        self.count_max = count_max
        self.queue = queue
        self.put = put
        self.debug = debug

    def run(self):
        global count
        global vid_count
        global paid_count
        GRID_LOCK.acquire()
        query_res = self.yt.query_episode(
            self.show['title'], self.name, 
            self.key[0], self.key[1], self.show['runtime'])
        count += 0.5
        GRID_LOCK.release()
        self.queue.put('data: %s\n\n' % ((count+6.)*1./(self.count_max+6.)*100))
        vids = self.yt.get_episode(query_res, debug=self.debug)
        GRID_LOCK.acquire()
        count += 0.5
        if vids:
            # Update episode info
            vid_count += 1
            paid_count += vids['paid']
            self.put.update_episode(self.show['title'], self.show['year'], 
                self.key[0], self.key[1], 
                'ytId', vids['id'])
            self.put.update_episode(self.show['title'], self.show['year'], 
                self.key[0], self.key[1], 
                'thumb', vids['snippet']['thumbnails']['default']['url'])
            self.put.update_episode(self.show['title'], self.show['year'], 
                self.key[0], self.key[1], 
                'paid', vids['paid'])
        GRID_LOCK.release()
        self.queue.put('data: %s\n\n' % ((count+6.)*1./(self.count_max+6.)*100))
        return


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
    # Start threading queue
    queue = Queue.Queue()
    # Threaded episode search and match
    for key, name in episodes.items():
        loop = EpisodeQuery(key=key, name=name, yt=yt, 
            show=show, count_max=count_max, 
            queue=queue, put=put, 
            debug=debug)
        loop.start()

    tcount = 0
    while tcount < len(episodes):
        if not queue.empty():
            out = queue.get(False)
            tcount += 1
            yield out
            queue.task_done()

    # Wait until queue done
    queue.join()

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


if __name__ == "__main__":
    title = sys.argv[1]
    run = run_query(title, cache=True, debug=False)
    for it in run:
        print it
