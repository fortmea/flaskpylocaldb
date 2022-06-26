import asyncio
import json
from os import mkdir, path
import shutil
from pylocaldatabase import pylocaldatabase
import atexit
from flask import Flask, request, escape, send_file
import shortuuid
from apscheduler.schedulers.background import BackgroundScheduler
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS, cross_origin
from requests import get, exceptions
from moviepy import editor as mov
keypath = "key.key"
dbcontroll = pylocaldatabase.databasecontroller(
    path="db.edb", isEncrypted=True)
scheduler = BackgroundScheduler()
app = Flask(__name__)
CORS(app)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["2000 per day", "150 per hour"]
)
print(__name__)


@app.route("/video")
def redditvideo():
    url = request.args.get("url")
    id = shortuuid.uuid()
    mkdir(id)
    exec = asyncio.run(get_video(url, id))
    shutil.rmtree(id)
    if exec!=False:
        return send_file("output/"+id+".mp4", mimetype='video/mp4')
    else:
        return False

def get_user_agent():
    # some fake one I found :/
    return 'Mozilla/5.0 (iPad; U; CPU OS 3_2_1 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Mobile/7B405'


async def get_video(url, id):

    try:  # checks if link is valid
        r = get(
            url + '.json',
            headers={'User-agent': get_user_agent()}
        )
    except exceptions.MissingSchema:
        return('Please provide a valid URL', 'error')

    if 'error' in r.text:
        if r.status_code == 404:
            return('Post not found', 'error')

    try:
        json_data = json.loads(r.text)[0]['data']['children'][0]['data']
    except json.decoder.JSONDecodeError:
        return('Post not found', 'error')

    try:  # checks if post contains video
        video_url = json_data['secure_media']['reddit_video']['fallback_url']

        video = get(video_url)
        videosize = video.headers['content-length']
        if(int(videosize) >= 225485783):
            return False

        videodata = video.content
        with open(id+'/video.mp4', 'wb') as file:
            file.write(videodata)
        audio = get_audio(json_data)
        with open(id+'/audio.aac', 'wb') as file:
            file.write(audio)
        print("ok")
        return stitch_video(id)
    except TypeError:
        return('Only posts with videos are supported', 'error')


def get_audio(json_data):
    try:
        audio_url = json_data['secure_media']['reddit_video']['hls_url'].split('HLS')[
            0]

        audio_url += 'HLS_AUDIO_160_K.aac'
        r = get(audio_url).content

        return r
    except TypeError:
        return('No audio found.', 'error')


def stitch_video(id):
    print(id)
    vid = mov.VideoFileClip(id+"/video.mp4")
    print("a")
    aud = mov.AudioFileClip(id+"/audio.aac")
    print(id)
    final = vid.set_audio(aud)
    aud.write_audiofile("output/"+id+".mp3")
    final.write_videofile("output/"+id+".mp4")
    return "ok"


@app.route("/")
def main():
    return "Olá, Mundo!"


@app.route("/comments/list/")
def comments():
    if dbcontroll.documentExists("comments"):
        if request.args.get("id"):
            data = json.dumps(dbcontroll.getDocument("comments").getItem(
                request.args['id']), default=pylocaldatabase.databasecontroller.serialize)
            # print(data)
            return data
        else:
            return json.dumps(dbcontroll.getDocument("comments").get(), default=pylocaldatabase.databasecontroller.serialize)
    else:
        return "No comments found."


@limiter.limit("5/minute", override_defaults=False)
@app.post("/comments/remove")
def removeUser():
    try:
        dbcontroll.getDocument("comments").removeItem(request.form['id'])
        return "200"
    except:
        return "400"


@limiter.limit("5/minute", override_defaults=False)
@app.post("/comments")
def addcoment():
    if dbcontroll.documentExists("comments") and (len(request.form['nome']) > 0) and (len(request.form['conteudo']) > 0):
        comments = dbcontroll.getDocument("comments")
        # print(request.form['pub'])
        item = comments.getItem(request.form['pub'])
        # print(item)
        if item == False:

            comments.insertItem(request.form['pub'], {})
        # print(comments.get())
        pub = comments.getItem(request.form['pub'])
        # print(pub)
        id = shortuuid.uuid()
        pub.insertProperty(id, generateComment(id, request.form))
        return "200"
    else:
        return "Error adding comment. Verify fields"


def generateComment(id, data={}):
    # print(data)
    return {'nome': escape(data['nome']), 'conteudo': escape(data['conteudo']), 'id': id}


def closing():
    dbcontroll.save_encrypted(keyPath=keypath)
    scheduler.shutdown()
    print("Byebye!")


def saveData():
    dbcontroll.save_encrypted(keyPath=keypath)
    shutil.rmtree(path.dirname(__file__)+"/output")
    mkdir("output")


@ app.before_first_request
def load():
    try:
        mkdir("output")
    except:
        True
    try:
        dbcontroll.decryptLoad(keyPath=keypath)
    except:
        dbcontroll.makeDatabase()
    if dbcontroll.documentExists("comments") == False:
        dbcontroll.insertDocument({}, "comments")
    atexit.register(closing)
    scheduler.add_job(func=saveData,
                      trigger="interval", seconds=60)
    scheduler.start()
    print("Ok. Database loaded")


if __name__ == "__main__":
    port = 80
    print("Listening on port - >", port)
    #app.run(host='0.0.0.0', port=port, debug=True)
    from waitress import serve
    serve(app, host='0.0.0.0', port=port)
