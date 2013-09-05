from flask import render_template
from app import app
import dbutils


@app.route('/')
@app.route('/index')
def index():
    series = dbutils.get_top6()
    return render_template("index.html", 
        series=series)


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/contact')
def contact():
    return render_template("contact.html")