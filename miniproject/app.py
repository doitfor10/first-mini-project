from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient

app = Flask(__name__)

# client = MongoClient('mongodb://test:test@localhost', 27017) 서버 올릴 때 쓰기
client = MongoClient('localhost', 27017)
db = client.dbrecipe

@app.route('/')
def home():
   return render_template('index.html')

if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)