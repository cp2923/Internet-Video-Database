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
from flask import Flask, request, render_template, g, redirect, Response
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

def checkdb(email, password):
    cmd = "SELECT * from users where email = :email and password = :password;"
    cursor = g.conn.execute(text(cmd), email=email, password=password)
    res = cursor.fetchone()
    if res == None:
        return False
    else:
        return True

@login_manager.user_loader
def user_loader(email):
    if email not in user_database:
        return

    print '@user_loader'
    user = User()
    user.id = email
    return user


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
        return '''
               <form action='login' method='POST'>
                <input type='text' name='email' id='email' placeholder='email'></input>
                <input type='password' name='pw' id='pw' placeholder='password'></input>
                <input type='submit' name='submit'></input>
               </form>
               '''
    print "@login"
    email = request.form['email']
    password = request.form['pw']
    if checkdb(email, password):
        user = User()
        user.id = email
        login_user(user)
        return 'Successful login'

    return 'Bad login'


@app.route('/videos')
def videos():
  cursor = g.conn.execute("SELECT * FROM videos ORDER BY dou DESC")
  names = []
  for result in cursor:
    names.append(result)  # can also be accessed using result[0]
  cursor.close()
  context = dict(data = names)
  return render_template("videos.html", **context)

@app.route('/profile')
def profile():
  cursor = g.conn.execute("SELECT * FROM users")
  names = cursor.fetchone()
  cursor.close()
  context = dict(data = names)
  return render_template("profile.html", **context)

@app.route('/changepassword', methods=['GET','POST'])
@login_required
def changepassword():
#  error = None
  email = request.form['email']
  old_pass = request.form['oldpassword']
  new_pass = request.form['newpassword']
  cursor = g.conn.execute('SELECT password FROM users WHERE email= %s', email)
  pass_db = str(cursor.fetchone()['password']) ## '123456' will be stored as u'123456' without str()
  cursor.close()
  if(old_pass == pass_db):
	g.conn.execute('UPDATE users SET password = %s WHERE email= %s',new_pass, email)
	return redirect('/profile')
#  error = 'Invalid Credentials'
  return  render_template("wrongpw.html")

@app.route('/towatch', methods=['GET','POST'])
def towatch():
  #email = request.form['email']
  #cursor = g.conn.execute('SELECT * FROM videos WHERE vid in (SELECT vid FROM wd  WHERE email =  %s)', email)

  cursor = g.conn.execute("SELECT * FROM videos ORDER BY dou DESC")
  names = []
  for result in cursor:
    names.append(result)  # can also be accessed using result[0]
  cursor.close()
  context = dict(cc = names)
  return render_template("towatch.html", **context)

# Example of adding new data to the database
@app.route('/register', methods=['POST'])
def register():
  #name = request.form['name']
  #print name
  #cmd = 'INSERT INTO users(email) VALUES (:email1)';
  #g.conn.execute(text(cmd), email1 = name);
  return redirect('/')


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
