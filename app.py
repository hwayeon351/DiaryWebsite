from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.elements import Null
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "DIARY"

db = SQLAlchemy(app)

class Diary(db.Model):
    diary_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False)
    img_path = db.Column(db.Text(), default='images/camera_icon.png')
    description = db.Column(db.Text())
    time = db.Column(db.DateTime(), nullable=False)

    def __init__(self, user_id):
        self.user_id = user_id
        self.time = datetime.now()

    def set_img_path(self, img_path):
        self.img_path = img_path
    
    def set_description(self, description):
        self.description = description

    def __repr__(self):
        return "<Diary('%d', '%s', '%s', '%s', '%s')>" % (self.diary_id, self.user_id, self.img_path, self.description, self.time)

class User(db.Model):
    user_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20), nullable=False)

    def __init__(self, user_id, name, phone, password):
        self.user_id = user_id
        self.name = name
        self.phone = phone
        self.password = password

    def __repr__(self):
        return "<User('%s', '%s', '%s', '%s')>" % (self.user_id, self.name, self.phone, self.password)


@app.route('/')
def login():
    diary = Diary.query.all()
    user = User.query.all()
    return render_template('login.html')

@app.route('/logout', methods = ['POST'])
def logout():
    if request.method == 'POST':
        if request.form['logout'] == 'SIGN OUT':
            flash('You have been successfully logged out!!')
            session.pop('user_id', None)
            session.pop('user_pw', None)
            return render_template('login.html')

@app.route('/login', methods = ['POST', 'GET'])
def check_user():
    if request.form['check'] == 'SIGN UP':
        return render_template('join.html')

    elif request.form['check'] == 'SIGN IN':
        id = request.form['user_id']
        pw = request.form['user_pw']
        query = db.session.query(User.query.filter(User.user_id==id, User.password==pw).exists()).scalar()
        if query:
            session['user_id'] = id
            session['user_pw'] = pw
            return redirect(url_for('home'))
        else:
            flash('ID or Password is incorrect!!')
            return render_template("login.html")

@app.route('/join', methods=['POST'])
def join():
    if request.form['check'] == 'CANCEL':
        return render_template('login.html')

    elif request.form['check'] == 'SIGN UP':
        if request.form['user_name'] == "" or request.form['user_phone'] == "" or request.form['user_pw'] == "" or request.form['user_id'] == "":
            flash('Please fill in all fields!!')
            return render_template('join.html')
        if db.session.query(User.query.filter(User.user_id==request.form['user_id']).exists()).scalar():
            flash('The ID already exists!!')
            return render_template('join.html')
        new_user = User(request.form['user_id'], request.form['user_name'], request.form['user_phone'], request.form['user_pw'])
        db.session.add(new_user)
        db.session.commit()
        flash('Success to sign up!!')
        return render_template('login.html')

    

@app.route('/home')
def home():
    diarys = db.session.query(Diary).filter_by(user_id=session['user_id']).order_by(Diary.time.desc()).all()
    return render_template('home.html', user_id = session['user_id'], diarys = diarys)

@app.route('/delete', methods=['POST'])
def delete():
    if request.form['check'] == 'DELETE':
        diary_id = request.form['diary_id']
        db.session.query(Diary).filter(Diary.diary_id==diary_id).delete()
        db.session.commit()
        flash('Success to delete a diary!!')
        return redirect(url_for('home'))

@app.route('/edit', methods=['POST'])
def edit():
    if request.form['check'] == 'EDIT':
        diary_id = request.form['diary_id']
        diary = db.session.query(Diary).filter(Diary.diary_id==diary_id).first()
        diary_description = diary.description
        if diary_description == "None": diary_description = ""
        return render_template('edit.html', diary_description = diary_description, diary_id = diary_id)
    elif request.form['check'] == 'CANCEL':
        return redirect(url_for('home'))
    elif request.form['check'] == 'SAVE':
        diary_id = request.form['diary_id']
        diary = db.session.query(Diary).filter(Diary.diary_id==diary_id).first()
        new_description = request.form['diary_description']
        new_img_path = 'images/' + request.files['diary_img'].filename

        if new_description == "" and new_img_path == 'images/':
            flash('Input picture or description for editing a diary!!')
            return render_template('edit.html', diary_id = diary_id)

        if new_img_path == 'images/':
            diary.set_description(new_description)
            db.session.commit()
        else:
            img = request.files['diary_img']
            if not os.path.exists("./static/images"):
                os.makedirs('./static/images')
            img.save("./static/images/"+secure_filename(img.filename))
            if new_description == "":
                diary.set_img_path(new_img_path)
                diary.set_description("None")
                db.session.commit()
            else:
                diary.set_img_path(new_img_path)
                diary.set_description(new_description)
                db.session.commit()

        flash("Success to edit the diary!!")
        return redirect(url_for('home'))

@app.route('/post', methods=['POST'])
def post():
    if request.form['check'] == 'POST NEW DIARY':
        return render_template('post.html')
    elif request.form['check'] == 'CANCEL':
        return redirect(url_for('home'))
    elif request.form['check'] == 'SAVE':
        new_description = request.form['diary_description']
        new_img_path = 'images/' + request.files['diary_img'].filename
        if new_description  == "" and new_img_path == 'images/':
            flash('Input picture or description for posting a diary!!')
            return render_template('post.html')
        if new_img_path == 'images/':
            diary = Diary(user_id=session['user_id'])
            diary.set_description(new_description)
            db.session.add(diary)
            db.session.commit()
        else:
            img = request.files['diary_img']
            if not os.path.exists("./static/images"):
                os.makedirs('./static/images')
            img.save("./static/images/"+secure_filename(img.filename))
            if new_description == "":
                diary = Diary(user_id=session['user_id'])
                diary.set_img_path(new_img_path)
                db.session.add(diary)
                db.session.commit()
            else:
                diary = Diary(user_id=session['user_id'])
                diary.set_img_path(new_img_path)
                diary.set_description(new_description)
                db.session.add(diary)
                db.session.commit()

        flash("Success to upload a diary!!")
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)