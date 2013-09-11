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
    