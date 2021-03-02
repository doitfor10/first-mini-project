from pymongo import MongoClient
import jwt #pyJWT
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('mongodb://54.180.145.121', 27017, username="test", password="test")
#client = MongoClient('mongodb://test:test@localhost', 27017)
# client = MongoClient('localhost', 27017)
db = client.dbrecipe
SECRET_KEY = 'KANGATOM'
@app.route('/')
def home():
   token_receive = request.cookies.get('mytoken')
   try:
      payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
      user_info = db.users.find_one({"id": payload["id"]})
      return render_template('recipe.html', user_info=user_info)
   except jwt.ExpiredSignatureError:
      return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
      # 서버 url_for은 함수 이름으로 받는다.
   except jwt.exceptions.DecodeError:
      return redirect(url_for("login"))

# 회원가입
@app.route('/main')
def login():
   return render_template('index.html')


# 로그인
@app.route('/login', methods=['POST'])
def login_user():

   id_receive = request.form['id_give']
   password_receive = request.form['password_give']

   pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
   result = db.users.find_one({'id':id_receive,'password':pw_hash})

   if result is not None:
      payload = {
         'id': id_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 1)
      }
      token = jwt.encode(payload,SECRET_KEY,algorithm='HS256')
      return jsonify({'result':'success','token':token})

   #찾지못할 때
   else:
      return jsonify({'result':'fail','msg':'아이디와 패스워드가 일치하지 않습니다.'})

# 회원가입
@app.route('/join')
def join():
   return render_template('register.html')

@app.route('/join/save', methods=['POST'])
def save_user():

   username_receive = request.form['username_give']
   id_receive = request.form['id_give']
   password_receive = request.form['password_give']
   password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

   doc = {
      "name": username_receive, # 닉네임
      "id": id_receive, # 아이디
      "password" : password_hash # 비밀번호
   }
   db.users.insert_one(doc)
   return jsonify({'result': 'success'})



@app.route('/register')
def write():
   token_receive = request.cookies.get('mytoken')
   try:
      payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
      user_info = db.users.find_one({"id": payload["id"]})
      return render_template('write.html', user_info=user_info)
   except jwt.ExpiredSignatureError:
      return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
      # 서버 url_for은 함수 이름으로 받는다.
   except jwt.exceptions.DecodeError:
      return redirect(url_for("login"))


# recipe 전체조회
@app.route('/recipe')
def recipeAll():
   return render_template('recipe.html')




if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)