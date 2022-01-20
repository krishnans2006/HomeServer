import codecs
import sqlite3

from camera_pi import Camera
from flask import Flask, redirect, url_for, render_template, request, session, g, flash, get_flashed_messages, Response

app = Flask(__name__)
app.config["SECRET_KEY"] = "pl,mkoijnbhuygvcftrdxszsewaq"


def get_db(database):
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(database)
    return db


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route("/")
def start():
    if "username" in session and "password" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login/", methods=["GET", "POST"])
def login():
    if "username" in session and "password" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        usr = request.form["username"]
        pwd = request.form["password"]
        if len(usr) < 1 or len(pwd) < 1:
            flash("0Please enter a username and password!")
            return redirect(url_for("login"))
        with app.app_context():
            cursor = get_db("homeserver.db").cursor()
            results = cursor.execute(f"SELECT password FROM users WHERE username='{usr}' LIMIT 1")
            for result in results:
                required_pwd = str(codecs.decode(bytes(result[0], "utf-8"), "base64", "strict"))[2:-1]
            try:
                if pwd == required_pwd:
                    session["username"] = usr
                    session["password"] = pwd
                    flash("1Successfully Logged In as {0}!".format(usr))
                    return redirect(url_for("dashboard"))
                else:
                    flash("0Invalid Username or Password!")
                    return redirect(url_for("login"))
            except:
                flash("0Invalid Username or Password!")
                return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/logout/")
def logout():
    try:
        del session["username"]
        del session["password"]
    finally:
        flash("1Successfully Logged Out!")
        return redirect(url_for("login"))


@app.route("/dashboard/")
def dashboard():
    if "username" in session and "password" in session:
        return render_template("dashboard.html")
    return redirect(url_for("login"))


@app.route("/video_feed/")
def video_feed():
    return Response(
        gen(Camera()),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    app.run(host="192.168.1.179", port="5555", threaded=True)
