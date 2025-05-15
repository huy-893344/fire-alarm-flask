import os
import time
import requests
import datetime
from threading import Thread

from flask import Flask, session, render_template, request, redirect, url_for
from waitress import serve
import paho.mqtt.client as mqtt

import firebase_admin
from firebase_admin import credentials, db

# 1. Khởi tạo Flask + SocketIO
app = Flask(__name__)
app.secret_key = os.urandom(24)


# 2. Khởi tạo Firebase Admin SDK
cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://tutrungtambaochay-default-rtdb.firebaseio.com/"
})
ref_data = db.reference("/DataSensorRealTime")
ref_alert = db.reference("/alert")

# 3. Cấu hình MQTT
mqtt_client = mqtt.Client()

# ===== Định nghĩa hàm callback =====
# ===== Khởi tạo MQTT client =====
mqtt_client = mqtt.Client()

# ===== Định nghĩa hàm callback =====
def on_connect(client, userdata, flags, rc):
    print("MQTT connected, code =", rc)
    client.subscribe("datasensor1")
    client.subscribe("datasensor2")
    client.subscribe("datasensor3")

def on_message(client, userdata, msg):
    # msg.topic ví dụ "datasensor1"
    sid = int(msg.topic[-1])              # 1, 2 hoặc 3
    parts = msg.payload.decode().split(",")
    addr  = parts[0]
    temp  = float(parts[1])
    hum   = float(parts[2])
    mq2   = float(parts[3])
    fire  = bool(int(parts[4]))

    # 1) Lưu lên Firebase
    send_data_firebase(sid, addr, temp, hum, mq2, fire)

    # 2) Emit realtime qua SocketIO
    socketio.emit(f"update_data_sensor{sid}", {
        "send_address": addr,
        "temperature": temp,
        "humidity": hum,
        "mq2": mq2,
        "fire": fire
    })

    # 3) Ghi alert nếu có cháy
    check_and_alert(sid, fire, addr)

# ===== Gán callback cho client =====
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# 4. Web API Key Firebase
FIREBASE_API_KEY = "AIzaSyA3mHhx4atZVfMe-cxgU3hbqHl3ieHuD4U"

# 5. Routes + Xác thực Firebase
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

# 6. Thread nền (nếu cần)
def background_task():
    while True:
        time.sleep(1)
thread = Thread(target=background_task, daemon=True)
thread.start()

# 7. Chạy ứng dụng
if __name__ == "__main__":
    mqtt_client.connect("broker.hivemq.com", 1883, 60)
    port = int(os.environ.get("PORT", 5000))
    serve(app, host="0.0.0.0", port=port)

