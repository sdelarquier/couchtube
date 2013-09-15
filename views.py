from flask import render_template
from flask import request
from flask import jsonify
from appct import app
import dbutils
import datagrab
import ytquery
import runquery
import json
import os


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
    show, _ = runquery.run_query(title)
    return jsonify(show)