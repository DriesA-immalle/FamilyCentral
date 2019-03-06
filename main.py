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

##########################
# START lOGIN AND SIGNUP #
##########################

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

########################
# END LOGIN AND SIGNUP #
########################

####################################
# START CREATE AND DELETE FAMILIES #
####################################

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

                cursor.execute('SELECT FamilyID FROM Family ORDER BY FamilyID DESC LIMIT 1;')
                SQLFamilyID = cursor.fetchone()[0]

                cursor.execute('UPDATE User SET FamilyID="' + str(SQLFamilyID) + '" WHERE UserID="' + str(user_id) + '";')
                cursor.execute('UPDATE User SET IsAdmin="1" WHERE UserID="' + str(user_id) + '";')
                database.commit()
                return redirect(url_for('familyPannel', familyID = SQLFamilyID))
    return render_template('createfamily.html')

@app.route('/deletefamily/', methods=['GET','POST'])
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
            if request.method == 'POST':
                print(f"[S] Family (ID: {SQLFamilyID}) was deleted")
                cursor.execute('DELETE FROM Family WHERE FamilyID=' + str(SQLFamilyID) + ';')
                cursor.execute('DELETE FROM Event WHERE FamilyID=' + str(SQLFamilyID) + ';')
                cursor.execute('DELETE FROM Invite WHERE FamilyID=' + str(SQLFamilyID) + ';')
                cursor.execute('DELETE FROM ShoppingListItem WHERE FamilyID=' + str(SQLFamilyID) + ';')
                cursor.execute('UPDATE User SET IsAdmin = 0 WHERE FamilyID="' + str(SQLFamilyID) + '";')
                cursor.execute('UPDATE User SET FamilyID = NULL WHERE FamilyId="' + str(SQLFamilyID) + '";')
                database.commit()
                return redirect(url_for('home'))    
            return render_template('deleteFamily.html')

##################################
# END CREATE AND DELETE FAMILIES #
##################################

##################
# START FAMILIES #
##################

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
        cursor.execute('DELETE FROM Event WHERE EventDate < date("now");')
        database.commit()
        cursor.execute('SELECT changes()')
        amount = cursor.fetchone()[0]
        print(f"[S] Deleted {amount} event(s) that expired")

        cursor.execute('SELECT FamilyName FROM Family WHERE FamilyID=' + str(SQLfamilyID) + ';')
        SQLFamilyName = cursor.fetchone()[0]

        cursor.execute('SELECT ItemName, Username, ItemID FROM ShoppingListItem WHERE FamilyID=' + str(SQLfamilyID) + ';')
        shoppinglistItems = cursor.fetchall()

        cursor.execute('SELECT EventName, EventDate, EventID FROM Event WHERE FamilyID=' + str(SQLfamilyID) + ';')
        events = cursor.fetchall()

        cursor.execute('SELECT * FROM Event WHERE FamilyID=' + str(SQLfamilyID) + ';')
        events = cursor.fetchall()
        amountevents = len(events)

        cursor.execute('SELECT IsAdmin FROM User WHERE UserID=' + str(user_id) + ';')
        isAdmin = cursor.fetchone()[0]

        cursor.execute('SELECT ItemName, Username, ItemID FROM ShoppingListItem WHERE FamilyID=' + str(SQLfamilyID) + ';')
        shoppinglistItems = cursor.fetchall()
        amountOfItems = len(shoppinglistItems)

        cursor.execute('SELECT ItemName, Username, ItemID FROM ShoppingListItem WHERE FamilyID=' + str(SQLfamilyID) + ';')
        notes = cursor.fetchall()
        amountofNotes = len(notes)

        print(f"[S] {session['username']} connected to the familypannel with ID {SQLfamilyID}")
        return render_template('family.html', familyName = SQLFamilyName, amountOfEvents = amountevents, amountOfItems = amountOfItems, amountOfNotes = amountofNotes, isAdmin = isAdmin)

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
    if familyID == None:
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

        cursor.execute('SELECT Username FROM User WHERE FamilyID=' + str(SQLfamilyID) + ';')
        members = cursor.fetchall()
        amountOfMembers = len(members)

        print(f"[S] {session['username']} (with ID {session['user_id']}) connected to the adminpannel")
        return render_template('familyAdminpannel.html', familyName = SQLFamilyName, amountOfMembers = amountOfMembers)

@app.route('/myfamily/<familyID>/admin/members')
@login_required
def adminMembers(familyID):
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']   

    cursor.execute('SELECT FamilyID FROM User WHERE UserID=' + user_id + ';')
    SQLfamilyID = cursor.fetchone()[0]

    cursor.execute('SELECT IsAdmin FROM User WHERE UserID=' + str(user_id) + ';')
    SQLIsAdmin = cursor.fetchone()[0]
    if familyID == None:
        return redirect(url_for('createFamily'))
    elif familyID != str(SQLfamilyID):
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to the wrong adminpannel")
        return redirect(url_for('adminMembers', familyID = SQLfamilyID))
    elif SQLIsAdmin == 0:
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to the adminpannel without permission")
        return redirect(url_for('familyPannel', familyID = SQLfamilyID))
    else:
        cursor.execute('SELECT userID, username FROM User WHERE FamilyID=' + str(SQLfamilyID) + ' AND UserID!=' + str(user_id) +  ';')
        users = cursor.fetchall()

        return render_template('adminMembers.html', users = users)

@app.route('/myfamily/<familyID>/admin/kickmember/<memberID>')
@login_required
def kickMember(familyID, memberID):
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']   

    cursor.execute('SELECT FamilyID FROM User WHERE UserID=' + user_id + ';')
    SQLfamilyID = cursor.fetchone()[0]

    cursor.execute('SELECT IsAdmin FROM User WHERE UserID=' + str(user_id) + ';')
    SQLIsAdmin = cursor.fetchone()[0]

    cursor.execute('SELECT FamilyID FROM User WHERE UserID=' + str(memberID) + ';')
    SQLMemberFamilyID = cursor.fetchone()[0]

    if familyID == None:
        return redirect(url_for('createFamily'))
    elif familyID != str(SQLfamilyID):
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to the wrong adminpannel")
        return redirect(url_for('kickMember', familyID = SQLfamilyID, memberID = memberID))
    elif SQLIsAdmin == 0:
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to the adminpannel without permission")
        return redirect(url_for('familyPannel', familyID = SQLfamilyID))
    elif SQLMemberFamilyID != SQLfamilyID:
        return redirect(url_for('adminMembers', familyID = SQLfamilyID))
    else:
        cursor.execute('UPDATE User SET IsAdmin = 0 WHERE UserID="' + str(memberID) + '";')
        cursor.execute('UPDATE User SET FamilyID = NULL WHERE UserId="' + str(memberID) + '";')
        database.commit()
        return redirect(url_for('adminMembers', familyID = SQLfamilyID))

@app.route('/leavefamily/<familyID>', methods=['GET', 'POST'])
@login_required
def leaveFamily(familyID):
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']

    cursor.execute('SELECT FamilyID FROM User WHERE UserID=' + user_id + ';')
    SQLfamilyID = cursor.fetchone()[0]
    if SQLfamilyID == None:
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried leaving a family but is not a member")
        return redirect(url_for('createFamily'))
    elif familyID != str(SQLfamilyID):
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried leaving another family")
        return redirect(url_for('leaveFamily', familyID = SQLfamilyID))
    else:
        if request.method == 'POST':
            cursor.execute('UPDATE User SET IsAdmin = 0 WHERE UserID="' + str(user_id) + '";')
            cursor.execute('UPDATE User SET FamilyID = NULL WHERE UserID="' + str(user_id) + '";')
            database.commit()
            return redirect(url_for('home', userID = user_id))
        return render_template('leaveFamily.html')
################
# END FAMILIES #
################

########################
# START ADDING MEMBERS #
########################

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

            if ' ' in email or ';' in email:
                print(f"[E] Possible attempt to SQL INJECTION")
                return render_template('addMember.html', Message='That user does not exist')

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

            cursor.execute('SELECT Familyname FROM Family WHERE FamilyID=' + str(SQLFamilyID) + ';')
            SQLFamilyName = cursor.fetchone()[0]

            cursor.execute('UPDATE User SET FamilyID="' + str(SQLFamilyID)  + '" WHERE UserID="' + str(user_id) + '";')
            database.commit()

            cursor.execute('DELETE FROM Invite WHERE InviteID=' + str(inviteID) + ';')
            database.commit()

            return render_template('joinFamily.html', familyname = SQLFamilyName)

######################
# END ADDING MEMBERS #
######################

################
# START EVENTS #
################

@app.route('/myfamily/<familyID>/events')
@login_required
def events(familyID):
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']

    cursor.execute('SELECT FamilyID FROM User WHERE UserID=' + user_id + ';')
    SQLfamilyID = cursor.fetchone()[0]

    cursor.execute('SELECT isAdmin FROM User Where UserID=' + user_id + ';')
    isAdmin = cursor.fetchone()[0]

    if SQLfamilyID == None:
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to a dashboard but is not in a family")
        return redirect(url_for('createFamily'))
    elif familyID != str(SQLfamilyID):
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to the wrong dashboard")
        return redirect(url_for('events', familyID = SQLfamilyID))
    else:
        cursor.execute('SELECT FamilyName FROM Family WHERE FamilyID=' + str(SQLfamilyID) + ';')
        SQLFamilyName = cursor.fetchone()[0]

        cursor.execute('SELECT EventName, EventDate, EventID FROM Event WHERE FamilyID=' + str(SQLfamilyID) + ';')
        events = cursor.fetchall()

        return render_template('events.html', familyName = SQLFamilyName, event = events, isAdmin = isAdmin)

@app.route('/myfamily/<familyID>/events/clearevent/<eventID>')
@login_required
def clearEvent(familyID, eventID):
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
        return redirect(url_for('clearEvent', familyID = SQLfamilyID, eventID = eventID))
    else:
        cursor.execute('DELETE FROM Event WHERE EventID=' + str(eventID) + ';')
        database.commit()
        return redirect(url_for('events', familyID = SQLfamilyID))

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
            return redirect(url_for('events', familyID = SQLfamilyID))
        return render_template('addEvent.html')

##############
# END EVENTS #
##############

######################
# START SHOPPINGLIST #
######################

@app.route('/myfamily/<familyID>/shoppinglist')
@login_required
def shoppinglist(familyID):
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']

    cursor.execute('SELECT FamilyID FROM User WHERE UserID=' + user_id + ';')
    SQLfamilyID = cursor.fetchone()[0]

    cursor.execute('SELECT isAdmin FROM User Where UserID=' + user_id + ';')
    isAdmin = cursor.fetchone()[0]

    if SQLfamilyID == None:
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to a dashboard but is not in a family")
        return redirect(url_for('createFamily'))
    elif familyID != str(SQLfamilyID):
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to the wrong dashboard")
        return redirect(url_for('shoppinglist', familyID = SQLfamilyID))
    else:
        cursor.execute('SELECT FamilyName FROM Family WHERE FamilyID=' + str(SQLfamilyID) + ';')
        SQLFamilyName = cursor.fetchone()[0]

        cursor.execute('SELECT ItemName, Username, ItemID FROM ShoppingListItem WHERE FamilyID=' + str(SQLfamilyID) + ';')
        shoppinglistItems = cursor.fetchall()

        return render_template('shoppinglist.html', familyName = SQLFamilyName, shoppinglist = shoppinglistItems, isAdmin = isAdmin)

@app.route('/myfamily/<familyID>/shoppinglist/addshoppinglist', methods=['GET', 'POST'])
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
            
            cursor.execute('SELECT Username FROM USER WHERE UserID=' + str(user_id) + ';')
            username = cursor.fetchone()[0]

            cursor.execute('INSERT INTO ShoppinglistItem(ItemName, Username, FamilyID) VALUES("' + str(item) + '","' + str(username) + '","' + str(SQLfamilyID) + '");') 
            database.commit()
            return redirect(url_for('shoppinglist', familyID = SQLfamilyID))
        return render_template('addShoppingList.html')

@app.route('/myfamily/<familyID>/shoppinglist/clearshoppinglist', methods=['GET', 'POST'])
@login_required
def clearShoppingList(familyID):
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
        return redirect(url_for('clearShoppingList', familyID = SQLfamilyID))
    else:
        if request.method == 'POST':
            cursor.execute('DELETE FROM ShoppinglistItem WHERE FamilyID="' + str(SQLfamilyID) + '";')
            database.commit()
            return redirect(url_for('shoppinglist', familyID = SQLfamilyID))
        return render_template('clearShoppinglist.html')

@app.route('/myfamily/<familyID>/shoppinglist/clearitem/<itemID>')
@login_required
def clearItem(familyID, itemID):
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']

    cursor.execute('SELECT FamilyID FROM User WHERE UserID=' + user_id + ';')
    SQLfamilyID = cursor.fetchone()[0]
    if SQLfamilyID == None:
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried deleting an item but is not in a family")
        return redirect(url_for('createFamily'))
    elif familyID != str(SQLfamilyID):
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to the wrong dashboard")
        return redirect(url_for('clearItem', familyID = SQLfamilyID, itemID = itemID))
    else:
        cursor.execute('DELETE FROM ShoppingListItem WHERE ItemID=' + str(itemID) + ';')
        database.commit()
        return redirect(url_for('shoppinglist', familyID = SQLfamilyID))

####################
# END SHOPPINGLIST #
####################

####################
# START NOTES #
####################

@app.route('/myfamily/<familyID>/notes')
@login_required
def notes(familyID):
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']

    cursor.execute('SELECT FamilyID FROM User WHERE UserID=' + user_id + ';')
    SQLfamilyID = cursor.fetchone()[0]
    if SQLfamilyID == None:
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried deleting an item but is not in a family")
        return redirect(url_for('createFamily'))
    elif familyID != str(SQLfamilyID):
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to the wrong dashboard")
        return redirect(url_for('notes', familyID = SQLfamilyID))
    else:
        cursor.execute('SELECT FamilyName FROM Family WHERE FamilyID=' + str(SQLfamilyID) + ';')
        SQLFamilyName = cursor.fetchone()[0]

        cursor.execute('SELECT isAdmin FROM User Where UserID=' + user_id + ';')
        isAdmin = cursor.fetchone()[0]

        cursor.execute('SELECT Note, Username, Importance, NoteID FROM Notes WHERE FamilyID=' + str(SQLfamilyID) + ' ORDER BY Importance;')
        notes = cursor.fetchall()

        return render_template('notes.html', notes = notes, familyName = SQLFamilyName, isAdmin = isAdmin)

@app.route('/myfamily/<familyID>/notes/addnote', methods=['GET', 'POST'])
@login_required
def addNote(familyID):
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
        return redirect(url_for('addNote', familyID = SQLfamilyID))
    else:
        if request.method == 'POST':
            note = request.form['note']
            importance = request.form['textInput']
            
            cursor.execute('SELECT Username FROM USER WHERE UserID=' + str(user_id) + ';')
            username = cursor.fetchone()[0]

            cursor.execute('INSERT INTO Notes(Note, Username, Importance, FamilyID) VALUES("' + str(note) + '","' + str(username) + '","' +str(importance) + '","' + str(SQLfamilyID) + '");') 
            database.commit()
            return redirect(url_for('notes', familyID = SQLfamilyID))
        return render_template('addNote.html')


@app.route('/myfamily/<familyID>/notes/clearnote/<noteID>')
@login_required
def clearNote(familyID, noteID):
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']

    cursor.execute('SELECT FamilyID FROM User WHERE UserID=' + user_id + ';')
    SQLfamilyID = cursor.fetchone()[0]
    if SQLfamilyID == None:
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried deleting an item but is not in a family")
        return redirect(url_for('createFamily'))
    elif familyID != str(SQLfamilyID):
        print(f"[E] {session['username']} (with ID {session['user_id']}) tried connecting to the wrong dashboard")
        return redirect(url_for('clearNote', familyID = SQLfamilyID, noteID = noteID))
    else:
        cursor.execute('DELETE FROM notes WHERE NoteID=' + str(noteID) + ';')
        database.commit()
        return redirect(url_for('notes', familyID = SQLfamilyID))
####################
# END NOTES #
####################

#################
# START ACCOUNT #
#################

@app.route('/myaccount/<userID>')
@login_required
def myAccount(userID):
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']

    cursor.execute('SELECT FamilyID FROM User WHERE UserID=' + user_id + ';')
    SQLfamilyID = cursor.fetchone()[0]
    if SQLfamilyID == None:
        inFamily = False
    else:
        inFamily = True

    if userID != user_id:
        return redirect(url_for('myAccount', userID = user_id))
    else:
        cursor.execute('SELECT * FROM User WHERE UserID=' + user_id + ';')
        user = cursor.fetchone()
        return render_template('myAccount.html', user = user, inFamily = inFamily)
        
@app.route('/deleteaccount/<userID>', methods=['GET', 'POST'])
@login_required
def deleteAccount(userID):
    database = connect('FamilyCentral')
    cursor = database.cursor()    
    user_id = session['user_id']

    if userID != user_id:
        return redirect(url_for('deleteAccount', userID = user_id))
    else:
        if request.method == 'POST':
            cursor.execute('DELETE FROM User WHERE UserID="' + str(user_id) + '";')
            cursor.execute('DELETE FROM Invite WHERE InvitedUserID="' + str(user_id) + '";')
            database.commit()
            logout_user()
            return redirect(url_for('home', userID = user_id))
        return render_template('deleteAccount.html')
###############
# END ACCOUNT #
###############

###############
# START ERROR #
###############

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#############
# END ERROR #
#############

if __name__ == "__main__":
    app.secret_key = 'TheSecretKey'
    app.run(debug=1, host='0.0.0.0')