# Thinking base python app with bootstrap ect to run
import requests
import ssl
import os
import time
import random
import pytz
import aiohttp
import json
from flask import Flask, render_template, request, flash, json, jsonify, send_from_directory, url_for, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Table, Column, Integer
from flask_session import Session
import redis

app = Flask(__name__,
            static_folder='static',
            static_url_path='/static',
            template_folder='templates')

# https://hackersandslackers.com/managing-user-session-variables-with-flask-sessions-and-redis/

app.secret_key = os.environ.get("SESSION_KEY")
app.config['SESSION_TYPE'] = 'redis'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///queenalphabet.sqlite3'


engine = create_engine("sqlite:///queenalphabet.sqlite3")

UPLOAD_FOLDER = './static/images'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)
# r = redis.from_url(
#     "redis://h:p6172946c3b02631a0bd95526b41b5042773915da3973338ca22f97a9f87c82b9@ec2-34-203-110-237.compute-1.amazonaws.com:22799")
r = redis.from_url(os.environ.get("REDIS_URL"))
app.config['SESSION_REDIS'] = r

sess = Session()
sess.init_app(app)


# https://requests.kennethreitz.org/en/master/user/advanced/#session-objects
s_test = requests.Session()

# def getSession():
#     return session.get('key', 'not set')
# def setSession():
#     session.set('key')=123
#     return 'ok'


class students(db.Model):
    id = db.Column('student_id', db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    city = db.Column(db.String(50))
    addr = db.Column(db.String(200))
    pin = db.Column(db.String(10))

    def __init__(self, name, city, addr, pin):
        self.name = name
        self.city = city
        self.addr = addr
        self.pin = pin


class users(db.Model):
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(50))

    def __init__(self, username, password):
        self.username = username
        self.password = password


class blogs(db.Model):
    id = db.Column('blog_id', db.Integer, primary_key=True)
    author = db.Column(db.String(100))
    date = db.Column(db.String(50))
    title = db.Column(db.String(500))
    blog = db.Column(db.String(100000))
    image = db.Column(db.String(10000))

    def __init__(self, author, date, title, blog, image):
        self.author = author
        self.date = date
        self.title = title
        self.blog = blog
        self.image = image


class subscribers(db.Model):
    id = db.Column('subscriber_id', db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))

    def __init__(self, name, email):
        self.name = name
        self.email = email


app.secret_key = os.urandom(12).hex()
app.config['DEBUG'] = True
app.logger.info('Started QA')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def return_index():
    if request.method == 'POST':
        if not request.form['name'] or not request.form['email']:
            flash('Please enter all the fields', 'error')
        else:
            subscriber = subscribers(
                request.form['name'], request.form['email'])

            db.session.add(subscriber)
            db.session.commit()

            flash(' You have successfully subscribed')
            return render_template('thanks.html', name=request.form['name'])
    return render_template('index.html')


@app.route('/blog')
def return_blog():
    return render_template('blog.html', blogs=blogs.query.all())


@app.route('/email_list')
def return_email_list():
    if session.get('logged_in') == True:
        emails = subscribers.query.with_entities(subscribers.email).all()
        return render_template('email_list.html', emails=emails)
    else:
        redirect(url_for('return_admin_login'))


@app.route('/thanks')
def return_thanks():
    return render_template('thanks.html')


@app.route('/preview_blog')
def return_preview():
    if session.get('logged_in') == True:
        return render_template('preview_blog.html')
    else:
        return redirect(url_for('return_admin_login'))


@app.route('/admin_login', methods=['GET', 'POST'])
def return_admin_login():
    print('trying to log in')
    if request.method == 'POST':
        if not request.form['username'] or not request.form['password']:
            flash('Please enter all the fields', 'error')
        else:
            username = request.form['username']
            password = request.form['password']

            Session = sessionmaker(bind=engine)
            s = Session()
            query = s.query(users).filter(users.username ==
                                          username, users.password == password)
            result = query.first()
            if result == None:
                print('failed the log in')
                session['logged_in'] = False
                # session.set('logged_in')=False
            else:
                print('logged in worked')
                session['logged_in'] = True
            #    session.set('logged_in')=True
                return redirect(url_for('admin_index'))
            # flash(' User logged in')

    return render_template('admin_login.html')


@ app.route('/lessons')
def return_lessons():
    return render_template('lessons.html')


@ app.route('/show_users', methods=['GET', 'POST', 'DELETE', 'PATCH'])
def show_users():
    if session.get('logged_in') == True:

        # if request.method == 'PATCH':
        #     print(request.form['Update'])
        #     clicked_username = request.form['Update']
        #     results = users.query.filter_by(username==clicked_username).first()

        #     print(results)
        #     return render_template('preview_blog.html', blog_test=results[0])
        # return render_template('show_users.html', users=users.query.all())
        if request.method == 'POST':

            clicked_username = request.form['Delete']
            print(clicked_username)
            results = users.query.filter(
                users.username == clicked_username).first()
            # print(results)
            db.session.delete(results)
            db.session.commit()
            return render_template('show_users.html', users=users.query.all())
        return render_template('show_users.html', users=users.query.all())

    return redirect(url_for('return_admin_login'))


@ app.route('/show_blogs', methods=['GET', 'POST'])
def show_blogs():
    if session.get('logged_in') == True:
        if request.method == 'POST':
            print(request.form['View'])
            clicked_title = request.form['View']
            results = blogs.query.filter(blogs.title == clicked_title).all()
            print(results)
            return render_template('preview_blog.html', blog_test=results[0])
        return render_template('show_blogs.html', blogs=blogs.query.all())
    else:
        return redirect(url_for('return_admin_login'))


@ app.route('/admin_index')
def admin_index():
    print('attempting admin index')
    if session.get('logged_in') == True:
        return render_template('admin_index.html')
    else:
        print('not logged in')
        return redirect(url_for('return_admin_login'))


@ app.route('/new_blogs', methods=['GET', 'POST'])
def new_blogs():
    if session.get('logged_in') == True:
        if request.method == 'POST':
            if request.form['submit_button'] == 'create':
                if not request.form['author'] or not request.form['date'] or not request.form['blog'] or not request.form['title']:
                    flash('Please enter all the fields', 'error')
                else:
                    if 'file' not in request.files:
                        flash('No file part')
                        return redirect(request.url)
                    file = request.files['file']
                    # if user does not select file, browser also
                    # submit an empty part without filename
                    if file.filename == '':
                        flash('No selected file')
                        return redirect(request.url)
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file.save(os.path.join(
                            app.config['UPLOAD_FOLDER'], filename))
                        # return redirect(url_for('show_blogs'))
                    blog = blogs(
                        request.form['author'], request.form['date'], request.form['title'], request.form['blog'], filename)

                    db.session.add(blog)
                    db.session.commit()

                    flash(' Blog record was successfully added')
                    return render_template('preview_blog.html', blog_test=blog)

        return render_template('new_blogs.html')
    else:
        return redirect(url_for('return_admin_login'))


@ app.route('/new_users', methods=['GET', 'POST'])
def new_users():
    if session.get('logged_in') == True:
        if request.method == 'POST':
            if not request.form['username'] or not request.form['password']:
                flash('Please enter all the fields', 'error')
            else:
                user = users(request.form['username'],
                             request.form['password'])

                db.session.add(user)
                db.session.commit()

                flash(' User record was successfully added')
                return redirect(url_for('show_users'))
        return render_template('new_users.html')
    else:
        return redirect(url_for('return_admin_login'))


if __name__ == "__main__":
    db.create_all()
    app.run()
