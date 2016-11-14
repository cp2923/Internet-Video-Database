
from flask import Flask, request, render_template, g, redirect, Response
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'super secret key'

login_manager = LoginManager()
login_manager.init_app(app)

######
# DATABASE CONNECTION
###########
from sqlalchemy import *
DATABASEURI = 'postgresql://cp2923:th2yz@104.196.175.120/postgres'

#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)

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
#######


# proxy for a database of users
user_database = {'pw@col': {'pw':'passwd'}, 'apple@col':{'pw':'passwd'}}

class User(UserMixin):
    pass
#############

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


@app.route("/",methods=["GET"])
def index():
    return Response(response="Hello World!",status=200)


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
    #if email in user_database and request.form['pw'] == user_database[email]['pw']:
    if checkdb(email, password):
        user = User()
        user.id = email
        login_user(user)
        return 'Successful login'

    return 'Bad login'


@app.route("/protected",methods=["GET"])
@login_required
def protected():
    return Response(response="{}:Hello Protected World!".format(current_user.id), status=200)

@app.route('/logout')
def logout():
    logout_user()
    return 'Logged out'

@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'

if __name__ == '__main__':
    import click

    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)#RECOMMENDED
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
