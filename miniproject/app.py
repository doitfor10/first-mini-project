from pymongo import MongoClient
import jwt #pyJWT
import datetime
import hashlib
import uuid
from flask import Flask, render_template, jsonify, request, redirect, url_for, json
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
      recipes = list(db.recipe.find({}).sort('like',-1))

      return render_template('recipe.html', user_info=user_info, recipes=recipes)
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


#등록 수행
@app.route('/register/recipe' , methods=['POST'])
def saveRecipe():

   title_receive = request.form["title_give"]
   desc_receive = request.form["desc_give"]
   url_give = request.form["url_give"]
   user_give = request.form["user_give"]

   if 'file_give' in request.files:
      file = request.files["file_give"]
      filename = secure_filename(file.filename)
      extension = filename.split(".")[-1]  # 뒤에서 첫번째 -1
      originName = file.filename.split(".")[0]
      file_path = f"recipe/{user_give}-{originName}-{uuid.uuid4()}.{extension}"
      file.save("./static/" + file_path)
      doc ={
         "title": title_receive,
         "desc": desc_receive,
         "img": file_path,
         "url": url_give,
         "user":user_give,
         "like": 0
      }
      db.recipe.insert_one(doc)

   return jsonify({"result":"success","msg":"레시피 등록이 되었습니다 :)"})



# 좋아요
@app.route('/like', methods=['POST'])
def like():

   token_receive = request.cookies.get('mytoken')
   try:
      payload = jwt.decode(token_receive,SECRET_KEY,algorithms=['HS256'])
      id = payload["id"] # 아이디 대상
      recipe = request.form['recipe_give'] # 음식 타이틀
      heart = request.form['heart_give'] # 하트 아이디
      like_user = db.like.find_one({'user_id':id,'recipe':recipe},{'_id':False})

      if like_user is None:
         doc ={
            'user_id':id,
            'recipe':recipe,
            'like':1,
            'heart':heart
         }
         db.like.insert_one(doc)
         target_recipe = db.recipe.find_one({'title':recipe},{'_id':False})
         current_like = target_recipe['like']
         new_like = current_like+1
         db.recipe.update_one({'title':recipe},{'$set':{'like':new_like}})
         return jsonify({'msg': '좋아요 완료!','do':'like','count':new_like})

      else:
         target_recipe = db.recipe.find_one({'title': recipe}, {'_id': False})
         current_like = target_recipe['like']

         if like_user['like'] == 0:
            db.like.update_one({'user_id':id,'recipe':recipe},{'$set':{'like':1}})
            user_like = current_like+1
            db.recipe.update_one({'title': recipe}, {'$set': {'like': user_like}})
            return jsonify({'msg': '좋아요 완료!','do':'like','count':user_like})
         

         db.like.update_one({'user_id': id,'recipe': recipe}, {'$set': {'like': 0}})
         user_like = current_like-1
         db.recipe.update_one({'title': recipe}, {'$set': {'like': user_like}})
         return jsonify({'msg': '좋아요 취소!','do':'unlike','count':user_like})

   except (jwt.ExpiredSignatureError,jwt.exceptions.DecodeError):
      return redirect(url_for("home"))

@app.route('/like/select', methods=['POST'])
def like_select():

   token_receive = request.cookies.get('mytoken')
   try:
      payload = jwt.decode(token_receive,SECRET_KEY,algorithms=['HS256'])
      id = payload["id"] # 아이디 대상
      user_like = list(db.like.find({"user_id":id, "like": 1},{'_id':False}))

      return jsonify({'like_id': user_like})
   except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
      return jsonify({'msg': '조회 실패'})


if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)