from flask import *
from flask_login import login_required, login_url, login_user, LoginManager, UserMixin, logout_user, current_user, AnonymousUserMixin
from sqlite3 import connect, Cursor
import time

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
  def __init__(self,id):
    self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
def redirectRootToHome():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        database = connect('FamilyCentral')
        cursor = database.cursor()

        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM USERS WHERE Email='" + email + "' AND Password='" + password + "';")
        data = cursor.fetchall()

        if len(data) == 0:
            print("[E] | " + time.strftime("%H:%M:%S") + " | incorrect credentials were inserted")
        else:
            cursor.execute("SELECT UserID FROM USERS WHERE Email ='" + email + "' AND Password = '" + password + "';")
            user_id = cursor.fetchone()[0]
            session['user_id'] = user_id

            cursor.execute("SELECT Username FROM USERS WHERE Email ='" + email + "' AND Password = '" + password + "';")
            name = cursor.fetchone()[0]
            session['username'] = name

            cursor.execute("SELECT Email FROM USERS WHERE Email ='" + email + "' AND Password = '" + password + "';")
            email = cursor.fetchone()[0]
            session['email'] = email

            login_user(User(user_id))
            print("[S] | " + time.strftime("%H:%M:%S") + " | User with name {} and ID {} was logged on".format(name, user_id))
            return redirect(url_for('family', id = session['user_id']))
    return render_template('login.html')

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        database = connect('FamilyCentral')
        cursor = database.cursor()

        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        cursor.execute('INSERT OR IGNORE INTO Users (username, email, password) VALUES ("' + username + '","' + email + '","' + password + '");')
        database.commit()

        if cursor.lastrowid == 0:
            print("[E] | " + time.strftime("%H:%M:%S") + " | new user with name {} not inserted due to duplicate data".format(username))
        else:
            print("[S] | " + time.strftime("%H:%M:%S") + " | new user with username {} and email {} was added".format(username, email))
    return render_template('signup.html')

@app.route('/createfamily')
@login_required
def createFamily():
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']

    cursor.execute('SELECT inFamily FROM Users WHERE UserID=' + user_id + ';')
    inFamily = cursor.fetchone()[0]
    
    if inFamily == 1:
        return render_template('alreadyinfamily.html')
    else:
        if request.method == 'POST':
            return redirect(url_for('home'))
        else:
            #TODO
            return render_template('createfamily.html')
            
@app.route('/myfamily')
@login_required
def family():
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']

    cursor.execute('SELECT InFamily FROM Users WHERE UserID=' + user_id + ';')
    inFamily = cursor.fetchone()[0]

    if inFamily == 0:
        return redirect(url_for('home'))
    else:
        cursor.execute('SELECT FamilyID FROM Users WHERE UserID=' + user_id + ';')
        familyID = cursor.fetchone()[0]

        return redirect(url_for('myfamily', familyID = familyID))

@app.route('/myfamily/<familyID>')
@login_required
def familyPannel(familyID):
    return render_template('family.html')

if __name__ == "__main__":
    app.secret_key = 'TheSecretKey'
    app.run(debug=1)