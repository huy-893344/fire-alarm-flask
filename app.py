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
    "project_id": "pham-quoc-anh-default-rtdb",
    "private_key_id": "f95c441ee047b10d2c165976d1093a48de378616",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQDCzHIVoWpV0Xa4\nTMXHipCewdQ3CqNRtrtPXqQRa3tNvXAvupqn0es/wqSdFPwU+f82MrfZVO4cMc55\nYLzMkRXIl7qcmfe/Cl6FnmeuKWNimrX6ad9C3Qf3tdu7PGIfglvb8pzIQy3Su+uh\nALCk6Nxy02W2oi70Bnqfaw6v7dQHpA05cyV5Rg2o8InfRsQgyD8NDNtItLTXqTEV\nvWLHbkDVaa96RbEvLg/Mx4sA2RcfmzCw+7hJsuvixVp8iZ00U6rvGl8JMT4om6LL\nWYEZ08Zot6XMA2fA37cjq4L0a/CUKfkcuXblXcYpejKfDMom0fzKAKHShY0VlDsH\nclIcIORnAgMBAAECggEAH/UJXEoUV0rbRqX1pmQxkJHs3jDFFVE8jmtQ0DjJTDoh\nTvs2hwSVquqkNc7tAgX3W+1bIvDfdUmofVok7wx4PeXCbBGIRtONKS+RA83va4xF\nAXVf9qirN3SivSdNU6z/o+g711DKEjHZGJsz34ICNGZA4ALgYBE2CbQ2/x6ts6jo\nwzrGFRCWY12Kyz4nfPJZQQZiWHWq8biiYhbNE+LKSeI8OXDvlzvI2diyUZR8pG/n\nO6JTBB+mcXSQWhSMDTHeaDzhpralvz09hwbiQbalFnH4qrELwkijDYg57apf3zlS\nt/+NXAuJubJ7JgGyJFjZ34RWT+Gj5TMUFYJlNtas3QKBgQD/QYme9U4Ml75OtpjR\nx5PSElmi7sUB31/XYa8WHIRK4bOYN4+DJa5YQjj37L87Iae5Z1tHpjJF4AkZhBGv\noMIOQCUEX0EXJ+SziI7qpRDDf75n/gmLhajW5BpcGfnQUeebi6i0q+mvyqec+Rh+\nPh4DilSV/B+5NssLC557ThrAVQKBgQDDXcwKW9sQP2DrgWxFfiafZrzOlpTpVQn5\n1h/eJWktQow3oH92VYRt8IBCqda7XICBEqiUZD7hxdn2TxUA7cDiuEkKDPinWEQ+\njkwHB8t0/BF9aSssW67BJckMVLG8N1NU+avH+/oTRPijO4ZDmRqv/I6JeyH8CuhZ\nSwWrXl3dywKBgQCvM5W5dJhAznrCXlSgUMNmgk/iJM82TNLk69iYbbRkDW0PArvP\ngbKcQ8AEdAyCEsSj3oxprmp9SZwVVnApQ0dPLrn5uUPdF/XDQO0Po4LRHUJc8KIu\nkOxlqyVoqC+uzDkTq5V9hS4eChRoCxXDuPEy7uTGGcrQfwp4p139NovoDQKBgQCK\nzHvnLCVx4KVaDCRBJwQHobUoTOFU+N7Siicv64JS7oGyD6wfBVjFxuVI92Mgz/JY\nQUpVyvbF7owRK1QvybqNGQKDSn3qXpJ1oyEuqYIKBf/jCrHqnOSGQvMYeJ+hqejh\naVR7C3E6+XhweBzGr+K+/37A/CND7vfuYJeRjcTAiwKBgQC/+eTkRUA8rV5idAOS\nhEPvCBJWsrBxKqVxcC9k2+J0SmiiwfDGmX2eginF+qvPKbRb4GlLKYiCkdbImkve\n3WQ6HenJbaUQU4suJOB6dlavwdh4k3lXcx2tnThRnjkaQB5fl3bHgWB462rQysev\nyEqBEsQqB8rzT6FgilC18lMCvA==\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-xyz12@pham-quoc-anh-default-rtdb.iam.gserviceaccount.com",
    "client_id": "123456789012345678901",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xyz12%40pham-quoc-anh-default-rtdb.iam.gserviceaccount.com"
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
