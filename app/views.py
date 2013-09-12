from flask import render_template
from flask import request
from flask import jsonify
from app import app
import dbutils
import datagrab
import ytquery
import json
import os

# whilte chapel

@app.route('/')
@app.route('/index')
def index():
    db = dbutils.DbGet()
    series = db.get_shows()
    db.close()
    series_json = []
    for show in series:
        series_json.append(
            {
                'title': show[0],
                'tokens': show[0].split(), 
                'episodes': str(show[3]),
                'ytcount': str(show[4])
            })
    with open(os.path.join(os.path.dirname(__file__), 'static/data/shows.json'),'w') as f:
        json.dump(series_json, f)
    return render_template("index.html", 
        series=series[:18])


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/contact')
def contact():
    return render_template("contact.html")


@app.route('/watch')
def watch():
    show = request.args.get('nm', '')
    year = request.args.get('yy', '')
    db = dbutils.DbGet()
    episodes = db.get_episodes(show, year)
    db.close()
    return render_template("result.html", 
        show=show, 
        year=year, 
        episodes=episodes,
        seasons=set([e[1] for e in episodes]))


@app.route('/findShow')
def findShow():
    show = request.args.get('title', '')
    data = datagrab.DataGrab(show)
    if data.show_title is not None:
        return jsonify(data.tvdb)
    else:
        return 'None'
    

@app.route('/ingestData')
def ingestData():
    title = request.args.get('title', '')
    # Open Push access to DB
    put = dbutils.DbPut()

    # Get merged data 
    merged = datagrab.DataMerge(title)
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
        vids = yt.get_episode(title, name, key[0], key[1])
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
    print '    Completed YouTube search and update'

    # Close DB access
    put.close()

    return jsonify(show)