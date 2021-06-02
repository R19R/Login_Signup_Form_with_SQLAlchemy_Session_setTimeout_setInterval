from operator import methodcaller
import re
from flask import Flask, json, redirect, render_template, request, jsonify, session, flash
from flask_session import Session
from flask_login.mixins import UserMixin
from flask_login.utils import _get_user
import sqlalchemy
from sqlalchemy.sql.expression import false
from models import UserModel, db, load_user, login
from flask_login import login_required, current_user, login_user, logout_user
import uuid, csv, os.path
# from sqlalchemy.orm import session
from sqlalchemy.sql import text
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session

app = Flask(__name__)
app.secret_key = 'xyz'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sess.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = "filesystem"
# Session(app)

login_manager = login
login_manager.init_app(app)
login_manager.login_view = 'login'

db.init_app(app)
@app.before_first_request
def create_table():
    db.create_all()


@app.route('/')
def home():
    return render_template('spa.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        log = request.get_json(force=True)
        uname = log.get('name')
        pword = log.get('password')
        session['user'] = uname
        user = UserModel.query.filter_by(username=uname).first()
        if user == None:
            return "No User"
        elif user is not None and user.check_password(pword):
            login_user(user)
            return "Login successful!"
        else:
            return "Wrong Credentials"
    return redirect("/")


@app.route("/newuser", methods=['GET', 'POST'])
def newuser():
    if request.method == "POST":
        new_user = request.get_json(force=True)
        username = new_user.get('name')
        password = new_user.get('password')
        con_password = new_user.get('confirm_pword')
        filename = "newfile_"+ username + ".csv"
        user = UserModel(username=username, filename=filename)
        user.set_password(password)
        with open(filename, 'a') as wfile:
                writer = csv.writer(wfile, lineterminator = '\n')
        db.session.add(user)
        db.session.commit()        
        return "User Created!"
    return "Method is GET"


@app.route('/logout')
def logout():
    if "user" in session:
        user = session['user']
        flash(f"You have been logged out, {user}", "info")
    session.pop("user", None)
    return redirect('/')


@app.route("/comments", methods=['GET', 'POST'])
def comments():
    f = session.get('user')
    
    filename = "newfile_"+ str(f) +".csv"

    det=[]

    if request.method == 'POST':
        fields = ["UID", "Name", "Comment"]
        params = request.get_json(force=True)
        name_r= params.get('name')
        comments_r = params.get('comment')
        uid = uuid.uuid4()
        with open(filename, 'a') as wfile:
            writer = csv.writer(wfile, lineterminator = '\n') 
            file_is_empty = os.stat(filename).st_size == 0
            if file_is_empty:
                writer.writerow(fields)
            writer.writerow([uid, name_r, comments_r])
        return jsonify({"UID":uid, "name":name_r, "comment":comments_r})
    else:
        with open(filename, 'r') as rfile:
            reader = csv.DictReader(rfile)
            for row in reader:
                detail = dict(row)
                det.append(detail)
            return jsonify(det)
        

if __name__ == "__main__":
    app.run(debug=True)