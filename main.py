from flask import *
from flask_login import login_required, login_url, login_user, LoginManager, UserMixin, logout_user, current_user, AnonymousUserMixin, current_user
from sqlite3 import connect, Cursor
import time
import hashlib

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
        hash = hashlib.sha256()

        email = request.form['email']   
        password = request.form['password']

        if ' ' in email or ';' in email:
            print(f"[E] Possible attempt to SQL INJECTION")
            return render_template('login.html', Message='That user does not exist')

        hash.update(password.encode('utf-8'))
        hashed = hash.hexdigest()
        print(hashed)
        print(email)
        cursor.execute("SELECT * FROM User WHERE Email='" + email + "' AND Password='" + hashed + "';")
        data = cursor.fetchall()

        if len(data) == 0:
            print(f"[E] Incorrect credentials (email: {email}) were inserted ")
            return render_template('login.html', Message = 'Unknown email and password combination')
        else:
            cursor.execute("SELECT UserID FROM User WHERE Email ='" + email + "' AND Password = '" + hashed + "';")
            user_id = cursor.fetchone()[0]
            session['user_id'] = user_id

            cursor.execute("SELECT Username FROM User WHERE Email ='" + email + "' AND Password = '" + hashed + "';")
            name = cursor.fetchone()[0]
            session['username'] = name

            cursor.execute("SELECT Email FROM User WHERE Email ='" + email + "' AND Password = '" + hashed + "';")
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
        hash = hashlib.sha256()

        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        if ' ' in username or ';' in username or ' ' in email or ';' in email:
            print(f"[E] Possible attempt to SQL INJECTION")
            return render_template('signup.html', Message='Only letters are allowed!')

        hash.update(password.encode('utf-8'))
        hashed = hash.hexdigest()

        print(hashed)
        print(email)

        cursor.execute('INSERT OR IGNORE INTO User (username, email, password) VALUES ("' + username + '","' + email + '","' + hashed + '");')
        database.commit()

        if cursor.lastrowid == 0:
            print(f"[E] Duplicate data (email: {email} / username: {username}) was inserted")
            return render_template('signup.html', Message='That email address or username is already in use')
        else:
            print(f"[S] New user with email {email} was inserted")
            return(redirect(url_for('login')))
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

            if ';' in FamilyName:
                return render_template('createfamily.html', Message='Only letters are allowed!')

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

@app.route('/deletefamily/')
@login_required
def deleteFamily():
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']

    cursor.execute('SELECT FamilyID FROM User WHERE UserID=' + user_id + ';')
    SQLFamilyID = cursor.fetchone()[0]

    cursor.execute('SELECT IsAdmin FROM User WHERE UserID=' + user_id + ';')
    SQLIsAdmin = cursor.fetchone()[0]

    if SQLFamilyID == None:
        print(f"[E] User with ID {user_id} is not part of a family")
        return redirect(url_for('home'))
    else:
        if SQLIsAdmin == 0:
            return redirect(url_for('familyPannel', familyID = SQLFamilyID))
        else:
            print(f"[S] Family (ID: {SQLFamilyID}) was deleted")
            cursor.execute('DELETE FROM Family WHERE FamilyID=' + str(SQLFamilyID) + ';')
            cursor.execute('UPDATE User SET IsAdmin = 0 WHERE FamilyID="' + str(SQLFamilyID) + '";')
            cursor.execute('UPDATE User SET FamilyID = NULL WHERE FamilyId="' + str(SQLFamilyID) + '";')
            database.commit()
        return redirect(url_for('home'))

@app.route('/myfamily/<familyID>/addmember', methods=['GET', 'POST'])
@login_required
def addMember(familyID):
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']

    cursor.execute('SELECT FamilyID FROM User WHERE UserID=' + user_id + ';')
    SQLFamilyID = cursor.fetchone()[0]

    if familyID != str(SQLFamilyID):
        return redirect(url_for('addMember', familyID = SQLFamilyID))
    else:
        if request.method == 'POST':
            email = request.form['email']

            cursor.execute('SELECT * FROM User WHERE Email="' + str(email) + '";')
            data = cursor.fetchall()

            if len(data) == 0:
                return render_template('addMember.html', Message = "We don't know that email")
            else:
                cursor.execute('SELECT FamilyID FROM User WHERE Email="' + str(email) + '";')
                SQLFamilyID = cursor.fetchone()[0]

                if SQLFamilyID != None:
                    return render_template('addMember.html', Message = "That user is already part of a family")
                else:
                    cursor.execute('SELECT UserID FROM User WHERE Email="' + str(email) + '";')
                    SQLUserID = cursor.fetchone()[0]

                    cursor.execute('INSERT INTO INVITE(FamilyID, InvitedUserID) VALUES("' + str(familyID) + '","' + str(SQLUserID) + '");')
                    database.commit()
                    
                    cursor.execute('SELECT InviteID FROM Invite ORDER BY InviteID DESC LIMIT 1')
                    InviteID = cursor.fetchone()[0]

                    link = '127.0.0.1:5000/invite/' + str(InviteID)

                    return render_template('addMember.html', InviteLink=link)
        return render_template('addMember.html')

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
        return redirect(url_for('createFamily'))
    elif familyID != str(SQLfamilyID):
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to the wrong dashboard")
        return redirect(url_for('familyPannel', familyID = SQLfamilyID))
    else:
        cursor.execute('SELECT FamilyName FROM Family WHERE FamilyID=' + str(SQLfamilyID) + ';')
        SQLFamilyName = cursor.fetchone()[0]

        cursor.execute('SELECT ItemName, UserID FROM ShoppingListItem WHERE FamilyID=' + str(SQLfamilyID) + ';')
        shoppinglistItems = cursor.fetchall()

        cursor.execute('SELECT EventName, EventDate FROM Event WHERE FamilyID=' + str(SQLfamilyID) + ';')
        events = cursor.fetchall()

        print(f"[S] {session['username']} connected to the familypannel with ID {SQLfamilyID}")
        return render_template('family.html', familyName = SQLFamilyName, event = events, shoppinglist = shoppinglistItems)

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
    if familyID != None:
        return redirect(url_for('createFamily'))
    elif familyID != str(SQLfamilyID):
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to the wrong adminpannel")
        return redirect(url_for('adminPannel', familyID = SQLfamilyID))
    elif SQLIsAdmin == 0:
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to the adminpannel without permission")
        return redirect(url_for('familyPannel', familyID = SQLfamilyID))
    else:
        cursor.execute('SELECT FamilyName FROM Family WHERE FamilyID=' + str(SQLfamilyID) + ';')
        SQLFamilyName = cursor.fetchone()[0]
        print(f"[S] {session['username']} (with ID {session['user_id']}) connected to the adminpannel")
        return render_template('familyAdminpannel.html', familyName = SQLFamilyName)

@app.route('/invite/<inviteID>')
@login_required
def invite(inviteID):
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id'] 

    cursor.execute('SELECT * FROM Invite WHERE InviteID=' + str(inviteID) + ';')
    data = cursor.fetchall()

    if len(data) == 0:
        print(f"[E] Invalid invite code ({inviteID}) was entered")
        return render_template('joinError.html', Message='That invite code is unknown')
    else:
        cursor.execute('SELECT InvitedUserID FROM Invite WHERE InviteID=' + str(inviteID) + ';')
        invitedUserID = cursor.fetchone()[0]

        if str(invitedUserID) != user_id:
            print(f"[E] Invite not valid for current user (ID: {user_id})")
            return render_template('joinError.html', Message='That invite is not meant for you')
        else:
            cursor.execute('SELECT FamilyID FROM Invite WHERE InviteID=' + str(inviteID) + ';')
            SQLFamilyID = cursor.fetchone()[0]

            cursor.execute('UPDATE User SET FamilyID="' + str(SQLFamilyID)  + '" WHERE UserID="' + str(user_id) + '";')
            database.commit()

            return render_template('joinFamily.html', Message='You are now a member of that family')

@app.route('/myfamily/<familyID>/addevent', methods=['GET', 'POST'])
@login_required
def addEvent(familyID):
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']

    cursor.execute('SELECT FamilyID FROM User WHERE UserID=' + user_id + ';')
    SQLfamilyID = cursor.fetchone()[0]
    if SQLfamilyID == None:
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to a dashboard but is not in a family")
        return redirect(url_for('createFamily'))
    elif familyID != str(SQLfamilyID):
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to the wrong dashboard")
        return redirect(url_for('addEvent', familyID = SQLfamilyID))
    else:
        if request.method == 'POST':
            name = request.form['name']
            date = request.form['date']
            
            cursor.execute('INSERT INTO EVENT(EventName, EventDate, FamilyID, UserID) VALUES("' + str(name) + '","' + str(date) + '","' + str(SQLfamilyID) + '","' + str(user_id) + '");') 
            database.commit()
            return redirect(url_for('familyPannel', familyID = SQLfamilyID))
        return render_template('addEvent.html')

@app.route('/myfamily/<familyID>/addshoppinglist', methods=['GET', 'POST'])
@login_required
def addShoppingList(familyID):
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']

    cursor.execute('SELECT FamilyID FROM User WHERE UserID=' + user_id + ';')
    SQLfamilyID = cursor.fetchone()[0]
    if SQLfamilyID == None:
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to a dashboard but is not in a family")
        return redirect(url_for('createFamily'))
    elif familyID != str(SQLfamilyID):
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to the wrong dashboard")
        return redirect(url_for('addShoppingList', familyID = SQLfamilyID))
    else:
        if request.method == 'POST':
            item = request.form['item']
            
            cursor.execute('INSERT INTO ShoppinglistItem(ItemName, UserID, FamilyID) VALUES("' + str(item) + '","' + str(user_id) + '","' + str(SQLfamilyID) + '");') 
            database.commit()
            return redirect(url_for('familyPannel', familyID = SQLfamilyID))
        return render_template('addShoppingList.html')

if __name__ == "__main__":
    app.secret_key = 'TheSecretKey'
    app.run(debug=1, host='0.0.0.0')