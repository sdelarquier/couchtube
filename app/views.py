from flask import render_template
from flask import request
from app import app
import dbutils
import ytquery


@app.route('/')
@app.route('/index')
def index():
    db = dbutils.DbGet()
    series = db.get_shows()
    db.close()
    return render_template("index.html", 
        series=series)


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/contact')
def contact():
    return render_template("contact.html")


@app.route('/watch')
def watch():
    # show = request.args.get('show', '')
    # year = request.args.get('year', '')
    # episodes = dbutils.get_episodes(show, year)
    # vids = ytquery.find_episodes(show, episodes)
    return render_template("result.html", )
        # show=show, 
        # year=year, 
        # episodes=zip(episodes, vids))
    