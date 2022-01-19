from base64 import b64encode as enc64
import flask_table
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_login import login_user, UserMixin, LoginManager, login_required, current_user, logout_user
from sqlalchemy import desc
from werkzeug.security import generate_password_hash, check_password_hash
from Scrap import scrap
import re
import json
import os
import os.path
import base64
from tables import URLHistoryTable, tagTable, StatTable

from config import SECRET_KEY


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key =SECRET_KEY
db = SQLAlchemy(app)
manager = LoginManager(app)


@manager.user_loader
def load_user(Users_id):
    return Users.query.get(Users_id)

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    Login = db.Column(db.String(16),nullable=False, unique=True)
    NickName = db.Column(db.String(16), nullable=False, unique=True)
    Passwords = db.Column(db.Text,nullable=False,)


class Pictures(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    NickName = db.Column(db.String(16), nullable=False)
    Date = db.Column(db.DateTime, default=datetime.utcnow)
    Size = db.Column(db.Integer)
    Byte = db.Column(db.Text )


class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    idImage = db.Column(db.Integer, nullable=False)
    NickName = db.Column(db.String(16), nullable=False)
    Text = db.Column(db.String(),nullable=False)
    Date = db.Column(db.DateTime, default=datetime.utcnow)


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    NickName = db.Column(db.String(16))
    Token = db.Column(db.String)
    Date = db.Column(db.DateTime, default=datetime.utcnow)
    URL = db.Column(db.String)







@app.route('/')
def rt():
    return home()


@app.route('/stat')
def stat():
    maxImage = (Pictures.query.all())
    maxComm = (Comments.query.all())
    maxSize=0
    dictByte, dictComment = [], []
    for comment in maxComm:
        dictComment.append(comment.Text)
    for image in maxImage:
        maxSize+=image.Size
        dictByte.append(image.Byte)
    UniqueImage = len(set(dictByte))
    UniqueComment = len(set(dictComment))
    name = ['a. Общее количество изображений',
            'b. Количество уникальных изображений',
            'c. Занимаемый размер в мб',
            'd. Общее количество комментариев',
            'e. Количество уникальных комментариев']
    answer =[str(len(maxImage)),
             str(UniqueImage),
             str(maxSize/1024/1024),
             str(len(maxComm)),
             str(UniqueComment)]
    _tagsTable = []
    for i in range(5):  _tagsTable.append(dict(_name=name[i], _answer=answer[i]))
    table = StatTable(_tagsTable)
    return table.__html__()

@app.route('/home')
def home():
    pictures = Pictures.query.order_by(desc(Pictures.Date)).all()
    comments = Comments.query.order_by(Comments.idImage).all()
    return render_template("Pictures.html", pictures=pictures, comments=comments)


@app.route('/addImage', methods=['GET', 'POST'])
@login_required
def addImage():
    imageData = request.files['file'].read()

    _user = current_user.NickName
    if _user:
        if imageData:
            pic = Pictures(NickName=_user, Date=datetime.now())
            try:
                db.session.add(pic)
                db.session.commit()
                Byte=enc64(imageData)
                Size = len(imageData)
                pic.Size=Size
                pic.Byte=Byte.decode('utf-8')
                db.session.commit()
                return redirect(url_for('home'))
            except Exception as e:
                print("Error:", e)
                return "Произошла ошибка при добавлении в базу данных"
        else:
            return home()
    else:
        return redirect(url_for('login'))


@app.route('/addComment/<int:id>', methods=['GET', 'POST'])
@login_required
def addComment(id):
    Comment = request.form['Comment']

    _user = current_user.NickName
    if _user:
        if Comment:
            com = Comments(NickName=_user, Text=Comment, idImage=id, Date=datetime.now())
            try:
                db.session.add(com)
                db.session.commit()
                return redirect(url_for('home'))
            except:
                return "При добавлении комментария произошла ошибка"
        else:
            return home()
    else:
        return redirect(url_for('login'))


@app.route('/checkUrlHistory', methods=['GET', 'POST'])
@login_required
def checkUrlHistory():
    rows = Ticket.query.filter(Ticket.NickName == current_user.NickName).all()
    historyTable = []
    for row in rows: historyTable.append(dict(_id=row.id, _url=row.URL, _date=row.Date))
    table = URLHistoryTable(historyTable)
    return table.__html__()


@app.route('/checkImageHistory', methods=['GET', 'POST'])
@login_required
def checkImageHistory():
    article = Pictures.query.filter(Pictures.NickName == current_user.NickName).all()
    return render_template("ImageHistory.html", pictures=article)


@app.route('/checkImageHistory/<string:NickName>/delet/<int:id>', methods=['GET', 'POST'])
@login_required
def deletImage(NickName, id):
    articlePic = Pictures.query.filter(Pictures.id == id ).first()
    articleComment = Comments.query.filter(Comments.idImage == id).all()
    try:
        os.remove(f"static\{str(id)}.jpg")
        db.session.object_session(articlePic).delete(articlePic)
        db.session.object_session(articlePic).commit()
        if articleComment:
            for comm in articleComment:
                db.session.object_session(comm).delete(comm)
                db.session.object_session(comm).commit()
        return redirect(url_for('checkImageHistory'))
    except:
        return redirect(url_for('checkImageHistory'))


@app.route('/checkImageHistory/<string:NickName>/update/<int:id>')
def updrateImage(NickName, id):
    img = Pictures.query.filter(Pictures.id == id).first()
    if (datetime.now()>(img.Date + timedelta(minutes=30))):
        try:
            img.Date = datetime.now()
            db.session.object_session(img).commit()
            return redirect(url_for('home'))
        except:
            return "Произошла ошибка"
    else:
        return f"Поднять можно будет в  {timedelta(minutes=30)+img.Date}"


@app.route('/checkCommentHistory', methods=['GET', 'POST'])
@login_required
def checkCommentHistory():
    commentsId = Comments.query.filter(Comments.NickName == current_user.NickName).all()
    PicturesId  = []
    for comm in commentsId:
        PicturesId.append(comm.idImage)
    UniquePicturestId=set(PicturesId)

    return render_template("CommentHistory.html",  comments=commentsId, pictures=UniquePicturestId)


@app.route('/checkCommentHistory/delet/<int:id>', methods=['GET', 'POST'])
@login_required
def deletComment(id):
    articleComment = Comments.query.filter(Comments.id == id).first()
    try:
        db.session.object_session(articleComment).delete(articleComment)
        db.session.object_session(articleComment).commit()
        return redirect(url_for('checkCommentHistory'))
    except:
        return redirect(url_for('checkCommentHistory'))


@app.route('/updateComment/<id>', methods=['GET', 'POST'])
@login_required
def updateComment(id):
    Comment = request.form['Comment']
    if Comment:
        com = Comments.query.filter(Comments.id == id).first()
        com.Text=Comment
        com.Date=datetime.now()
        try:
            db.session.object_session(com).commit()
            return redirect(url_for('checkCommentHistory'))
        except:
            return "При изменении произошла ошибка"
    else:
        return redirect(url_for('checkCommentHistory'))


@app.route('/account',  methods=['POST', 'GET'])
@login_required
def Account():
    if request.method == 'POST' and request.form['URL']:
        URL = request.form['URL']
        Token, mistake =scrap(URL)
        if mistake ==('404'):
            return "Невозможно перейти по ссылки"
        ticket = Ticket(URL=URL, Token=str(Token), NickName=current_user.NickName)
        try:
            db.session.add(ticket)
            db.session.commit()
            return f"Ваш id = {str(ticket.id)}"
        except:
            return "При добавлении URL произошла ошибка"
    else:
        return render_template("Account.html", NickName=current_user.NickName)


@app.route('/token', methods=['POST', 'GET'])
def tag():
    if request.method == 'POST' :
        if("ID_Token" in request.form):
            tags = Ticket.query.filter(Ticket.id == request.form['ID_Token']).first()
            if tags:
                tagDict = json.loads(tags.Token.replace("'",'"'))
                _tagsTable = []
                for key in tagDict:  _tagsTable.append(dict(_tag=key, _count=tagDict[key]["count"], _nested=tagDict[key]["nested"]))
                table = tagTable(_tagsTable)
                return table.__html__()
            else:
                return "Такого ID не существует"
    else:
        return render_template("Token.html")


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST' and request.form['Login'] and request.form['Password']:
        user=Users.query.filter(Users.Login == request.form['Login']).first()
        if user and check_password_hash(user.Passwords, request.form['Password']):
            login_user(user)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('Account'))
        else:
             flash('Ошибка в данных, авторизация не удалась')

    return render_template("Login.html")


@app.route('/registration',methods=['POST', 'GET'])
def registration():
    def CheckPassword(password: str) -> bool:
        L = (len(password) > 4, re.search(r'[a-z]', password), re.search(r'[A-Z]', password), re.search(r'\d', password),
             len(password) < 17)
        return all(L)
    if request.method == 'POST' and request.form['Login'] and request.form['Password'] and request.form['NickName']:
        if (len(request.form['NickName'])>2 and len(request.form['Login'])>3 and request.form['Password'] != request.form['Login']
        and CheckPassword(request.form['Password']) and len(request.form['Login'])<17) and len(request.form['NickName'])<17 and request.form['NickName'] != request.form['Login']:
            hash = generate_password_hash(request.form['Password'])
            users = Users(NickName=request.form['NickName'], Passwords=hash, Login=request.form['Login'] )
            try:
                db.session.add(users)
                db.session.commit()
                flash('Поздравляю с успешной регистрацией')
                return redirect(url_for('login'))
            except:
                flash('Такой Логин или Никнейм уже используются')
                return render_template("Registration.html")
        else:
            flash('Данные введены не верно')
            return render_template("Registration.html")
    else:
        return render_template("Registration.html")


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.after_request
def redirect_to_signin(response):
    if response.status_code == 401:
        return redirect(url_for('login') + '?next=' + request.url)
    return response

if __name__ == '__main__':
    from main import db
    db.create_all()
    app.run(debug=True)