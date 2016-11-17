#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import IntegrityError, DataError
from flask import Flask, request, render_template, g, redirect, Response, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

app.secret_key = 'super secret key'

login_manager = LoginManager()
login_manager.init_app(app)
#
# The following uses the postgresql test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of:
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/postgres
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# Swap out the URI below with the URI for the database created in part 2
#DATABASEURI = "sqlite:///test.db"
DATABASEURI = 'postgresql://cp2923:th2yz@104.196.175.120/postgres'

#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)
#engine.execute('''SELECT * FROM users''')
#
# START SQLITE SETUP CODE
#
# after these statements run, you should see a file test.db in your webserver/ directory
# this is a sqlite database that you can query like psql typing in the shell command line:
#
#     sqlite3 test.db
#
# The following sqlite3 commands may be useful:
#
#     .tables               -- will list the tables in the database
#     .schema <tablename>   -- print CREATE TABLE statement for table
#
# The setup code should be deleted once you switch to using the Part 2 postgresql database
#
#engine.execute("""DROP TABLE IF EXISTS test;""")
#engine.execute("""CREATE TABLE IF NOT EXISTS test (
#  id serial,
#  name text
#);""")
#engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
#
# END SQLITE SETUP CODE
#



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
class User(UserMixin):
    pass

def checkdb(email, password):
    cursor = g.conn.execute('SELECT * from users where LOWER(email) = LOWER(%s) and password = %s',email, password)
    res = cursor.fetchone()
    cursor.close()
    if res == None:
        return False
    else:
        return str(res['email'])


@login_manager.user_loader
def user_loader(email):
    cursor = g.conn.execute('SELECT * FROM users WHERE email= %s', email)
    res = cursor.fetchone()
    cursor.close()
    if res == None:
        return

    user = User()
    user.id = email
    return user

@app.route('/logout')
def logout():
    logout_user()
    return render_template("index.html")

@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("index.html")
    email = request.form['email']
    password = request.form['password']
    uid = checkdb(email, password)
    if uid:
        user = User()
        user.id = uid
        login_user(user)
        return redirect("/profile")
    else:
        return render_template("wrong.html")

@app.route('/videos')
def videos():
  cursor = g.conn.execute("SELECT v.name, round(avg(r.rating),1), v.nov, v.nol, v.nod, v.vid, v.genre FROM videos as v LEFT JOIN reviews as r ON v.vid=r.vid GROUP BY v.vid, v.dou, v.nov, v.nol, v.nod, v.vid, v.genre ORDER BY v.dou DESC")
  names = []
  for result in cursor:
    names.append(result)  # can also be accessed using result[0]
  cursor.close()
  context = dict(data = names)
  return render_template("videos.html", **context)

@app.route('/top',methods=['GET', 'POST'])
def top():
  cursor = g.conn.execute("SELECT v.name, round(avg(r.rating),1), v.nov, v.nol, v.nod, v.vid, v.genre FROM videos as v,reviews as r WHERE v.vid=r.vid GROUP BY v.vid, v.dou, v.nov, v.nol, v.nod, v.vid, v.genre ORDER BY avg(r.rating) DESC LIMIT 5 ")
  names = []
  for result in cursor:
    names.append(result)  # can also be accessed using result[0]
  cursor.close()
  context = dict(data = names)
  return render_template("videos.html", **context)

@app.route('/video', methods=['GET'])
def video():
  vid = int(request.args.get('videoID'))
  cursor = g.conn.execute("SELECT * FROM users as u, videos as v, reviews as r WHERE v.vid=r.vid AND v.vid= %s AND u.email=r.email ORDER BY dor DESC", vid)
  names = []
  for result in cursor:
    names.append(result)  # can also be accessed using result[0]
  cursor.close()
  context = dict(data = names)
  return render_template("video.html", **context)


@app.route('/profile')
@login_required
def profile():
  email = current_user.id
  cursor = g.conn.execute("SELECT * FROM users WHERE email = %s", email)
  names = cursor.fetchone()
  cursor.close()
  context = dict(data = names)
  return render_template("profile.html", **context)

@app.route('/changepassword', methods=['GET','POST'])
@login_required
def changepassword():
#  error = None
  email = current_user.id
  old_pass = request.form['oldpassword']
  new_pass = request.form['newpassword']
  cursor = g.conn.execute('SELECT * FROM users WHERE email= %s', email)
  result = cursor.fetchone()
  cursor.close()
  pass_db = str(result['password']) ## '123456' will be stored as u'123456' without str()
  context = dict(data=result)
  if(old_pass == pass_db):
	g.conn.execute('UPDATE users SET password = %s WHERE email= %s',new_pass, email)
	return redirect('/profile')
#  error = 'Invalid Credentials'
  return  render_template("wrongpw.html", **context)

@app.route('/towatch', methods=['GET','POST'])
@login_required
def towatch():
  email = current_user.id
  cursor = g.conn.execute('SELECT * FROM videos WHERE vid in (SELECT vid FROM wl  WHERE email =  %s)', email)

  #cursor = g.conn.execute("SELECT * FROM videos ORDER BY dou DESC")
  names = []
  for result in cursor:
    names.append(result)  # can also be accessed using result[0]
  cursor.close()
  context = dict(data = names)
  return render_template("towatch.html", **context)

@app.route('/watched', methods=['GET','POST'])
@login_required
def watched():
  email = current_user.id
  cursor = g.conn.execute('SELECT * FROM videos WHERE vid in (SELECT vid FROM wd  WHERE email =  %s)', email)

  #cursor = g.conn.execute("SELECT * FROM videos ORDER BY dou DESC")
  names = []
  for result in cursor:
    names.append(result)  # can also be accessed using result[0]
  cursor.close()
  context = dict(data = names)
  return render_template("watched.html", **context)

@app.route('/removewatched', methods=['POST'])
@login_required
def removewatched():
  email = current_user.id
  r_list = request.form.getlist('remove')
  for r in r_list:
    g.conn.execute('DELETE FROM wd WHERE vid = %s AND email = %s', (r,email))
  return redirect('watched')


@app.route('/removetowatch', methods=['POST'])
@login_required
def removetowatch():
  email = current_user.id
  r_list = request.form.getlist('remove')
  for r in r_list:
    g.conn.execute('DELETE FROM wl WHERE vid = %s AND email = %s', (r,email))
  return redirect('towatch')

@app.route('/playlists')
def playlists():
  cursor = g.conn.execute("SELECT * FROM playlist as p,users as u WHERE p.email = u.email")
  names = []
  for result in cursor:
    names.append(result)  # can also be accessed using result[0]
  cursor.close()
  context = dict(data = names)
  return render_template("playlists.html", **context)

@app.route('/playlist', methods=['GET','POST'])
def playlist():
  pid = int(request.args.get('playlistID'))
  cursor = g.conn.execute('SELECT * FROM videos as v,vbp WHERE v.vid = vbp.vid AND pid =  %s', pid)

  names = []
  for result in cursor:
    names.append(result)  # can also be accessed using result[0]
  cursor.close()
  context = dict(data = names)
  return render_template("playlist.html", **context)

@app.route('/addwatch', methods=['POST'])
@login_required
def addwatch():
    email = current_user.id
    r_list = request.form.getlist('add')
    if "Add to Watchlist" in request.form.get('action'):
        for r in r_list:
            try:
                g.conn.execute('INSERT INTO wl (email, vid) VALUES (%s, %s)',email,r)
            except (IntegrityError, DataError):
                pass
        return redirect('/towatch')
    elif 'Add to Watched' in request.form.get('action'):
        for r in r_list:
            try:
                g.conn.execute('INSERT INTO wd (email, vid) VALUES (%s, %s)',email,r)
            except (IntegrityError, DataError):
                pass
        return redirect('/watched')
    else:
        try:
            plname = request.form.get('action')
            if plname == '':
                return redirect('/videos')
            else:
                cursor = g.conn.execute('SELECT pid FROM playlist WHERE name = %s AND email =  %s', plname, email)
                result = cursor.fetchone()
                cursor.close()
                if result == None:
                    cursor = g.conn.execute('SELECT pid FROM playlist ORDER BY pid DESC')
                    pid = int(cursor.fetchone().values()[0]) + 1
                    print(pid)
                    cursor.close()
                    g.conn.execute('INSERT INTO playlist (pid, name, email) VALUES (%s, %s, %s)', pid, plname, email)
                cursor = g.conn.execute('SELECT pid FROM playlist WHERE name = %s AND email =  %s', plname, email)
                for result in cursor:
                    pid = result.values()[0]
                    for r in r_list:
                        try:
                            g.conn.execute('INSERT INTO vbp (vid, pid) VALUES (%s, %s)',str(r),result.values()[0])
                        except (IntegrityError, DataError):
                            pass
                cursor.close()
                return redirect(url_for('myplaylist', playlistID = pid))
        except(ValueError):
            pass


@app.route('/myplaylists', methods=['GET','POST'])
@login_required
def myplaylists():
  email = current_user.id
  cursor = g.conn.execute('SELECT * FROM playlist WHERE email =  %s', email)

  names = []
  for result in cursor:
    names.append(result)  # can also be accessed using result[0]
  cursor.close()
  context = dict(data = names)
  return render_template("myplaylists.html", **context)

@app.route('/removeplaylists', methods=['POST'])
@login_required
def removeplaylists():
  r_list = request.form.getlist('remove')
  for r in r_list:
    g.conn.execute('DELETE FROM playlist WHERE pid = %s', r)
  return redirect('myplaylists')

@app.route('/myplaylist', methods=['GET','POST'])
@login_required
def myplaylist():
  pid = int(request.args.get('playlistID'))
  cursor = g.conn.execute('SELECT * FROM videos as v,vbp WHERE v.vid = vbp.vid AND pid =  %s', pid)

  names = []
  for result in cursor:
    names.append(result)  # can also be accessed using result[0]
  cursor.close()
  context = dict(data = names)
  return render_template("myplaylist.html", **context)


@app.route('/removeplaylist', methods=['POST'])
@login_required
def removeplaylist():
  pid = int(request.form.get('playlistID'))
  r_list = request.form.getlist('remove')
  for r in r_list:
    g.conn.execute('DELETE FROM vbp WHERE pid = %s AND vid = %s', (pid,r))
  return redirect(url_for('myplaylist', playlistID = pid))

@app.route('/myreviews')
@login_required
def myreviews():
  email = current_user.id
  cursor = g.conn.execute('SELECT * FROM reviews as r,videos as v WHERE r.vid=v.vid AND r.email =  %s', email)

  #cursor = g.conn.execute("SELECT * FROM videos ORDER BY dou DESC")
  names = []
  for result in cursor:
    names.append(result)  # can also be accessed using result[0]
  cursor.close()
  context = dict(data = names)
  return render_template("myreviews.html", **context)

@app.route('/removereviews', methods=['POST'])
@login_required
def removereviews():
  email = current_user.id
  r_list = request.form.getlist('remove')
  for r in r_list:
    g.conn.execute('DELETE FROM reviews WHERE vid = %s AND email = %s', (r,email))
  return redirect('myreviews')


# Example of adding new data to the database
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template("index.html")
    email = request.form['email']
    password = request.form['password']
    dob = request.form['dob']
    name = request.form['name']
    try:
        g.conn.execute('INSERT INTO users (email, password, name, dob) VALUES (%s,%s,%s,%s)',email, password, name, dob)
        return 'Successful registered'
    except (IntegrityError, DataError):
        return render_template("wrong.html")

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
