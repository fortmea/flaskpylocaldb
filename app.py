import json
from pylocaldatabase import pylocaldatabase
import atexit
from flask import Flask, request, escape
import shortuuid
dbcontroll = pylocaldatabase.databasecontroller(path="database.json")
app = Flask(__name__)


@app.route("/")
def main():
    return "Olá, Mundo!"


@app.route("/users")
def users():
    if dbcontroll.documentExists("users"):
        return json.dumps(dbcontroll.getDocument("users").get(), default=pylocaldatabase.databasecontroller.serialize)
    else:
        return "No users found."


@app.post("/users")
def adduser():
    print(dbcontroll.getDocument("users"))
    print(dbcontroll.documentExists("users"))
    if dbcontroll.documentExists("users") and (len(request.form['nome']) > 0):
        users = dbcontroll.getDocument("users")
        users.insertItem(shortuuid.uuid(), generateUser(request.form))
        return "200"
    else:
        return "Error adding user."


def generateUser(data={}):
    print(data)
    return {'nome': escape(data['nome']), 'email': escape(data['email']), 'senha': escape(data['senha'])}

def closing():
    dbcontroll.save()
    print("Byebye!")



@app.before_first_request
def load():
    try:
        dbcontroll.load()
    except:
        dbcontroll.makeDatabase()
    if dbcontroll.documentExists("users") == False:
        dbcontroll.insertDocument({}, "users")
    atexit.register(closing)
    print("ok")
