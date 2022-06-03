import json
from pylocaldatabase import pylocaldatabase
import atexit
from flask import Flask, request, escape
import shortuuid
from apscheduler.schedulers.background import BackgroundScheduler
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS, cross_origin

dbcontroll = pylocaldatabase.databasecontroller(path="database.json")
scheduler = BackgroundScheduler()
app = Flask(__name__)
CORS(app)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["20000 per day", "1500 per hour"]
)
print(__name__)


@app.route("/")
def main():
    return "Olá, Mundo!"


@app.route("/comments/list/")
def comments():
    if dbcontroll.documentExists("comments"):
        if request.args.get("id"):
            data = json.dumps(dbcontroll.getDocument("comments").getItem(
                request.args['id']), default=pylocaldatabase.databasecontroller.serialize)
            print(data)
            return data
        else:
            return json.dumps(dbcontroll.getDocument("comments").get(), default=pylocaldatabase.databasecontroller.serialize)
    else:
        return "No comments found."


# def checkUserEmail(email):
#    users = dbcontroll.getDocument("users").get()
#    for x in users:
#        if users.get(x).get()['email'] == email:
#            return True
#        else:
#            return False


@app.post("/comments/remove")
def removeUser():
    try:
        dbcontroll.getDocument("comments").removeItem(request.form['id'])
        return "200"
    except:
        return "400"


# @app.post("/users/update")
# def upduser():
#    try:
#        user = dbcontroll.getDocument("users").getItem(request.form['id'])
#        nUserData = generateComment(request.form)
#        for x in nUserData:
#            user.insertProperty(x, nUserData[x])
#        return "200"
#    except:
#        return "400"

@limiter.limit("1/second", override_defaults=False)
@app.post("/comments")
def addcoment():
    if dbcontroll.documentExists("comments") and (len(request.form['nome']) > 0) and (len(request.form['conteudo']) > 0):
        comments = dbcontroll.getDocument("comments")
        print(request.form['pub'])
        item = comments.getItem(request.form['pub'])
        if item == 'false':
            comments.insertItem(request.form['pub'], {})

        pub = comments.getItem(request.form['pub'])
        id = shortuuid.uuid()
        pub.insertProperty(id, generateComment(id, request.form))
        return "200"
    else:
        return "Error adding comment. Verify fields"


def generateComment(id, data={}):
    print(data)
    return {'nome': escape(data['nome']), 'conteudo': escape(data['conteudo']), 'id': id}


def closing():
    dbcontroll.save()
    scheduler.shutdown()
    print("Byebye!")


@ app.before_first_request
def load():

    try:
        dbcontroll.load()
    except:
        dbcontroll.makeDatabase()
    if dbcontroll.documentExists("comments") == False:
        dbcontroll.insertDocument({}, "comments")
    atexit.register(closing)
    scheduler.add_job(func=dbcontroll.save,
                      trigger="interval", seconds=60)
    scheduler.start()
    print("ok")
