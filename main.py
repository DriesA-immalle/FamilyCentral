from flask import *
from flask_login import login_required, login_url, login_user, LoginManager, UserMixin, logout_user, current_user, AnonymousUserMixin
from sqlite3 import connect, Cursor

app = Flask(__name__)
database = connect('FamilyCentral')
cursor = database.cursor()
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
        pass
    return render_template('login.html')

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        pass
    return render_template('signup.html')

@app.route('/myfamily')
@login_required
def family():
    return render_template('family.html')

if __name__ == "__main__":
    app.secret_key = 'TheSecretKey'
    app.run(debug=1)