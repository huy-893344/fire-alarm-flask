import os
import time
import requests
import datetime
from threading import Thread

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from waitress import serve

import firebase_admin
from firebase_admin import credentials, db

# 1. Khởi tạo Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)

# 2. Khởi tạo Firebase Admin SDK
cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://tutrungtambaochay-default-rtdb.firebaseio.com/"
})
ref_data = db.reference("/DataSensorRealTime")
ref_alert = db.reference("/alert")

# 3. Web API Key Firebase
FIREBASE_API_KEY = "AIzaSyA3mHhx4atZVfMe-cxgU3hbqHl3ieHuD4U"

# 4. Routes + Xác thực Firebase
@app.route("/", methods=["GET"])
def FUN_root():
    if "username" not in session:
        return redirect(url_for("FUN_login"))
    return render_template("base.html")

@app.route("/register", methods=["GET","POST"])
def FUN_register():
    error = None
    if request.method == "POST":
        email = request.form["username"]
        pwd   = request.form["password"]
        conf  = request.form["confirm"]
        if pwd != conf:
            error = "Mật khẩu không khớp"
        else:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
            data = {"email": email, "password": pwd, "returnSecureToken": True}
            r = requests.post(url, json=data)
            if r.status_code == 200:
                return redirect(url_for("FUN_login"))
            error = r.json().get("error", {}).get("message", "Lỗi đăng ký")
    return render_template("register.html", error=error)

@app.route("/login", methods=["GET","POST"])
def FUN_login():
    error = None
    if request.method == "POST":
        email    = request.form["username"]
        password = request.form["password"]
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
        data = {"email": email, "password": password, "returnSecureToken": True}
        r = requests.post(url, json=data)
        if r.status_code == 200:
            session["username"] = email
            return redirect(url_for("FUN_dashboard"))
        error = r.json().get("error", {}).get("message", "Sai user hoặc mật khẩu")
    return render_template("login.html", error=error)

@app.route("/logout")
def FUN_logout():
    session.pop("username", None)
    return redirect(url_for("FUN_login"))

@app.route("/dashboard")
def FUN_dashboard():
    if "username" not in session:
        return redirect(url_for("FUN_login"))
    return render_template("viewdata.html")

@app.route("/userhome")
def FUN_userhome():
    if "username" not in session:
        return redirect(url_for("FUN_login"))
    return render_template("userhome.html")

@app.route("/setting", methods=["GET","POST"])
def FUN_setting():
    if "username" not in session:
        return redirect(url_for("FUN_login"))
    msg = None
    if request.method == "POST":
        msg = "Đã lưu cài đặt"
    return render_template("setting.html", msg=msg)

# 5. API cung cấp dữ liệu realtime cho JavaScript polling
@app.route("/api/realtime")
def api_realtime():
    data = ref_data.get() or {}
    return jsonify(data)

# 6. Thread nền (tuỳ chọn)
def background_task():
    while True:
        time.sleep(1)
thread = Thread(target=background_task, daemon=True)
thread.start()

# 7. Chạy Flask qua Waitress
if __name__ == "__main__":
    mqtt_client.connect("broker.hivemq.com", 1883, 60)
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    serve(app, host="0.0.0.0", port=port)
