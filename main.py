from flask import *
from flask_login import login_required, login_url, login_user, LoginManager, UserMixin, logout_user, current_user, AnonymousUserMixin, current_user
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
    return render_template('home.html', user = current_user)

@app.route('/login/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        database = connect('FamilyCentral')
        cursor = database.cursor()

        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM User WHERE Email='" + email + "' AND Password='" + password + "';")
        data = cursor.fetchall()

        if len(data) == 0:
            print(f"[E] Incorrect credentials (email: {email}) were inserted ")
            return render_template('login.html', Message = 'Unknown email and password combination')
        else:
            cursor.execute("SELECT UserID FROM User WHERE Email ='" + email + "' AND Password = '" + password + "';")
            user_id = cursor.fetchone()[0]
            session['user_id'] = user_id

            cursor.execute("SELECT Username FROM User WHERE Email ='" + email + "' AND Password = '" + password + "';")
            name = cursor.fetchone()[0]
            session['username'] = name

            cursor.execute("SELECT Email FROM User WHERE Email ='" + email + "' AND Password = '" + password + "';")
            email = cursor.fetchone()[0]
            session['email'] = email

            login_user(User(user_id))
            print(f"[S] {session['username']} with ID {session['user_id']} was logged on")

            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/signup/', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        database = connect('FamilyCentral')
        cursor = database.cursor()

        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        cursor.execute('INSERT OR IGNORE INTO User (username, email, password) VALUES ("' + username + '","' + email + '","' + password + '");')
        database.commit()

        if cursor.lastrowid == 0:
            print(f"[E] Duplicate data (email: {email} / username: {username}) was inserted")
            return render_template('signup.html', Message='That email address or username is already in use')
        else:
            print(f"[S] New user with email {email} was inserted")
    return render_template('signup.html')

@app.route('/createfamily/', methods=['GET','POST'])
@login_required
def createFamily():
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']

    cursor.execute('SELECT FamilyID FROM User WHERE UserID=' + user_id + ';')
    SQLFamilyID = cursor.fetchone()[0]

    if SQLFamilyID != None:
        print(f"[E] User with ID {user_id} is already part of a family")
        return redirect(url_for('familyPannel', familyID = SQLFamilyID))
    else:
        if request.method == 'POST':
            FamilyName = request.form['familyName']

            cursor.execute('INSERT OR IGNORE INTO Family(FamilyName) VALUES("' + FamilyName + '");')
            database.commit()

            if cursor.lastrowid == 0:
                print(f"[E] Duplicate data (name: {FamilyName}) was not inserted")
            else: 
                print(f"[S] New family (name: {FamilyName}) was inserted")
                
                cursor.execute('SELECT FamilyID FROM Family WHERE FamilyName="' + FamilyName + '";')
                SQLFamilyID = cursor.fetchone()[0]

                cursor.execute('UPDATE User SET FamilyID="' + str(SQLFamilyID) + '" WHERE UserID="' + str(user_id) + '";')
                cursor.execute('UPDATE User SET IsAdmin="1" WHERE UserID="' + str(user_id) + '";')
                database.commit()
                return redirect(url_for('familyPannel', familyID = SQLFamilyID))
    return render_template('createfamily.html')

@app.route('/myfamily/<familyID>')
@login_required
def familyPannel(familyID):
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']

    cursor.execute('SELECT FamilyID FROM User WHERE UserID=' + user_id + ';')
    SQLfamilyID = cursor.fetchone()[0]
    if SQLfamilyID == None:
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to a dashboard but is not in a family")
        return redirect(url_for('home'))
    elif familyID != str(SQLfamilyID):
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to the wrong dashboard")
        return redirect(url_for('familyPannel', familyID = SQLfamilyID))
    else:
        cursor.execute('SELECT FamilyName FROM Family WHERE FamilyID=' + str(SQLfamilyID) + ';')
        SQLFamilyName = cursor.fetchone()[0]
        print(f"[E] {session['username']} connected to the familypannel with ID {SQLfamilyID}")
        return render_template('family.html', familyName = SQLFamilyName)

@app.route('/myfamily/<familyID>/admin')
@login_required
def adminPannel(familyID):
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']   

    cursor.execute('SELECT FamilyID FROM User WHERE UserID=' + user_id + ';')
    SQLfamilyID = cursor.fetchone()[0]

    cursor.execute('SELECT IsAdmin FROM User WHERE UserID=' + str(user_id) + ';')
    SQLIsAdmin = cursor.fetchone()[0]
    if familyID != str(SQLfamilyID):
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to the wrong adminpannel")
        return redirect(url_for('adminPannel', familyID = SQLfamilyID))
    elif SQLIsAdmin == 0:
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to the adminpannel without permission")
        return redirect(url_for('familyPannel', familyID = SQLfamilyID))
    else:
        cursor.execute('SELECT FamilyName FROM Family WHERE FamilyID=' + str(SQLfamilyID) + ';')
        SQLFamilyName = cursor.fetchone()[0]
        print(f"[E] {session['username']} (with ID {session['user_id']}) connected to the adminpannel")
        return render_template('familyAdminpannel.html', familyName = SQLFamilyName)

if __name__ == "__main__":
    app.secret_key = 'TheSecretKey'
    app.run(debug=1)