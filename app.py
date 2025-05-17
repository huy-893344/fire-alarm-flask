#!/usr/bin/env python3
# app.py

import os
import datetime
import firebase_admin
from firebase_admin import credentials, db
import paho.mqtt.client as mqtt
import serial
import time

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from flask_cors import CORS

# ========== FIREBASE CONFIGURATION (Embed service account info directly) ==========
# Paste your entire JSON service account key below, preserving line breaks
service_account_info = {
    "type": "service_account",
    "project_id": "pham-quoc-anh",
    "private_key_id": "6cc08ab4d0fadeb56cd6692238ee771af648e68d",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCRCk/QwrWiL1VO\ni+xgzPUpQcG33sUtKQHhP0P4DpxtZHaA7DKSo56RpXB9r/VKwNqFWqUU6iH/1T3h\n8tETwkv6WbxpRZ9C6z85BVxt5V+7rLqizFMj8vD9JRXADZCg6S1ZQA9NFf6qfR2t\n10zubIgHiC9tRLGuNXaXS1izkQWFK6BHDltYuxEo2COZWoJtrWjIRO1iHpBUwkRB\nBHja5s6sRef7oQeKxRmjU6nCXG6X75vb0bToBFpWI0lyehwavjmVJTzg3c81UG3W\n00NTKDovu6+YXdRsAAQ+0WetEUYGmh8bO9zz3EjfrNIr6BXpaK7rWCYVsT+78ubt\nzD/PxeKjAgMBAAECggEAGUqXCGwriBCA66Vynp6e0Ybp5Movz+Qqs8B4dbT2igzO\nrUSCvRdS+0rCBui7+UEP2dkomDELpLTmiZPx6WQkI4+qTyEY2G51I9hPecpZmzxP\nfzvp84bVhw8Eb+ztn2GJytpk0KhZNBmFJ183xwud3NJekss7wIkKGO/Gk+lh8Qqb\nPX7qP2LfY1mYuiYiB4xood2/BgQ1OSm8m+Z3o6ROoe1iBK9yCjYBtBjNy62IF6WK\nEI6XQ0exNyl9HWHKFhlWDptdjd7u+hNDn0k8lZz9A8G2ehYkomC3eT/32F84azEE\nTaRjqUTeyRCgsOMN6RFdlFUw1XJT1mvd74lOF2HzYQKBgQDEUDDzg6fpXFAnySCf\nbn51QIb9BxhMRrU4GQrUl8Wd1TnlsZC1pqmeX1GaFTuanfR8JiPihZ24bbMhh5bX\nyIfXt2OG3RoDpKr00w+WTYUQVg1FBmtX/W2Vf92P3uTvIG9SkWYeVWkwSDtYdD4N\n9bWVIXOai4+meABjdLfsLdVxhQKBgQC9I1maaEUXtb/lJi6uoVAZ1HrOIcjQbzSc\n65o5IztN6VNsyF+PDcW7YBZy2471A58mvdF9CfwU5WurZIFuQi+okMErdV9UXlP7\n9ZZtsons/f/oBVgJXjvVTIpDrnlhr+yf8geJFoH4HIThWxvEHl4YrONxlbWBxbOD\nfIBabVcoBwKBgHjMO4LspXsEMdJ5gZh5PllaDnZOUlZFQCe3ySFODuzzEwBTBg+w\n8TihwK3GmPmobpOiSHyP6aBd6FcefuRi4awMjbKkBOju/79MzI+ZPeLygJHTxGPN\nbwwKNUTdTBQU6kttauAJgIOUPuhMBw9B/a05e1BCxm8R8nNAlBhBj9CdAoGAfza3\nndNkJX5pg4ca/vohFj6EGwE+QHOLv7/4C1ZXHSBCrHhZTa7FwDHw53Alx0aYVUZ3\nENMWajelI7KGG9MImyhBxSk85VJMyrt0YnQjsPNmnHh7rlFjjSPeG4fOvJXHYg04\nZExvPqJv/eN52X9TauVeVZeMbay8AURMUIYaiSECgYEAryYyyPK3kSfxB4SPpBsy\nX0oXpfnubY1Rn8j+VjB2Gcw7NbxKTsLL5wjSCorMr1/on7n911Sq9B8r4+VBmfak\nK+poLEWxgohgNYU5W4N2rdy4fWqwpGzplHD7AjidONDlUrzYAMnyy94Skg5C6KDu\n8j0j6c9UjNvZtPBqBdpnHfE=\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@pham-quoc-anh.iam.gserviceaccount.com",
    "client_id": "102006103166067369217",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40pham-quoc-anh.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# Initialize Firebase Admin SDK with embedded credentials
cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://pham-quoc-anh-default-rtdb.firebaseio.com"
})

# ========== MQTT and Sensor Data Handling ==========
def send_realtime_firebase(sid, addr, temp, hum, gas, fire):
    ref = db.reference(f"/DataSensorRealTime/{sid}")
    data = {
        "send_address": addr,
        "temperature": temp,
        "humidity": hum,
        "mq2": gas,
        "fire": fire,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    ref.set(data)

# ========== MQTT CONFIG (nếu có) ==========
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT   = 1883
MQTT_TOPICS = [("datasensor1",0), ("datasensor2",0)]

def on_connect(client, userdata, flags, rc):
    for topic, qos in MQTT_TOPICS:
        client.subscribe(topic, qos)

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        sid, addr, t, h, g, f = payload.split(",")
        send_realtime_firebase(sid, addr, float(t), float(h), float(g), int(f))
    except:
        pass

# Khởi động MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()


# ========== FLASK APP ==========
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_me")
CORS(app)

# In-memory user store
# Lưu trữ tạm
users = {"anh066214@gmail.com": "123456"}
t_system_settings = {"threshold": 2500, "alert_email": ""}

# Home: redirect to login
@app.route("/")
def index():
    return redirect(url_for("login"))

# ---- LOGIN ----
@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email","").strip()
        pw    = request.form.get("password","").strip()
        if email in users and users[email] == pw:
            session["email"] = email
            return redirect(url_for("dashboard"))
        error = "Sai tài khoản hoặc mật khẩu"
    return render_template("login.html", error=error)

# ---- REGISTER ----
@app.route("/register", methods=["GET","POST"])
def register():
    error = None
    if request.method == "POST":
        email   = request.form.get("email","").strip()
        pw      = request.form.get("password","")
        confirm = request.form.get("confirm","")
        if pw != confirm:
            error = "Mật khẩu không khớp"
        elif email in users:
            error = "Email đã tồn tại"
        else:
            users[email] = pw
            flash("Đăng ký thành công! Mời bạn đăng nhập.", "success")
            return redirect(url_for("login"))
    return render_template("register.html", error=error)

# ---- DASHBOARD ----
@app.route("/dashboard")
def dashboard():
    if "email" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

# ---- SETTING ----
t_system_settings = {"threshold":2500, "alert_email":""}

@app.route("/setting", methods=["GET","POST"])
def setting():
    if "email" not in session:
        return redirect(url_for("login"))
    message = None
    if request.method == "POST":
        try:
            t_system_settings["threshold"]  = int(request.form.get("threshold", 2500))
            t_system_settings["alert_email"] = request.form.get("alert_email","")
            message = "Lưu cấu hình thành công"
        except:
            message = "Lỗi khi lưu cấu hình"
    return render_template("setting.html",
                           settings=t_system_settings,
                           message=message)

# ---- CONTACT ----
@app.route("/contact", methods=["GET","POST"])
def contact():
    message = None
    if request.method == "POST":
        name    = request.form.get("name","").strip()
        email   = request.form.get("email","").strip()
        content = request.form.get("message","").strip()
        message = f"Cảm ơn {name}, chúng tôi đã nhận phản hồi!"
    return render_template("contact.html", message=message)

# ---- LOGOUT ----
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---- API for realtime data ----
@app.route("/api/realtime")
def api_data():
    data = db.reference("/DataSensorRealTime").get() or {}
    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
