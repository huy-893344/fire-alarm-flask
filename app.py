#!/usr/bin/env python3
# app.py

import os
import datetime
import firebase_admin
from firebase_admin import credentials, db
import paho.mqtt.client as mqtt
import serial
import time
from flask import Flask, render_template, request, redirect, url_for, session
from flask_cors import CORS

# ========== CONFIGURATION ==========
# Firebase Realtime Database setup (cần dùng đúng URL dự án của bạn)
cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://tutrungtambaochay-default-rtdb.firebaseio.com"
})

def send_realtime_firebase(sid, addr, temp, hum, gas, fire):
    """
    Push dữ liệu trực tiếp lên root của database với key theo sid
    Ví dụ: esp32_temp, esp32_humi, esp32_mq2, esp32_fire
    """
    root_ref = db.reference('/')  # trỏ đến gốc
    payload = {
        f"{sid}_temp": temp,
        f"{sid}_humi": hum,
        f"{sid}_mq2":  gas,
        f"{sid}_fire": fire,
        # nếu muốn lưu thêm metadata:
        f"{sid}_addr": addr,
        f"{sid}_timestamp": datetime.datetime.utcnow().isoformat()
    }
    # Cập nhật các key ngay tại root
    root_ref.update(payload)
    print(f"[{sid}] Updated root keys: {', '.join(payload.keys())} @ {payload[f'{sid}_timestamp']}")

# SIM module serial config
try:
    sim_serial = serial.Serial("COM7", 9600, timeout=1)
except serial.SerialException:
    sim_serial = None

phone_number = "+849xxxxxxxx"

# MQTT config
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT   = 1883
MQTT_TOPICS = [("datasensor1", 0), ("datasensor2", 0), ("datasensor3", 0)]

# In-memory user store
users = {"anh066214@gmail.com": "123456"}

# In-memory system settings
# (ngưỡng gas nếu cần vào code, ở đây không dùng để lưu root)
t_system_settings = {"threshold": 2500, "alert_email": ""}

# SMS sending
def send_sms(content):
    if sim_serial and sim_serial.is_open:
        try:
            sim_serial.write(b'AT\r'); time.sleep(0.5)
            sim_serial.write(b'AT+CMGF=1\r'); time.sleep(0.5)
            sim_serial.write(f'AT+CMGS="{phone_number}"\r'.encode()); time.sleep(0.5)
            sim_serial.write(content.encode() + b'\x1A'); time.sleep(2)
            print("SMS sent:", content)
        except Exception as e:
            print("SMS sending error:", e)
    else:
        print("SIM module not available, cannot send SMS.")

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code", rc)
    for topic, qos in MQTT_TOPICS:
        client.subscribe(topic, qos)


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        sid, addr, temp, hum, gas, fire = payload.split(",")
        temp = float(temp)
        hum  = float(hum)
        gas  = float(gas)
        fire = int(fire)
    except Exception as e:
        print("Failed parsing MQTT message:", e, msg.payload)
        return

    # Push to Firebase
    send_realtime_firebase(sid, addr, temp, hum, gas, fire)

    # Send SMS if alert condition met
    if fire == 1 or gas >= t_system_settings.get("threshold", 2500):
        send_sms(f"CẢNH BÁO: Node {sid}@{addr} - Gas={gas}ppm, Fire={fire}")

# Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_me")
CORS(app)

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        pw    = request.form.get("password")
        if email in users and users[email] == pw:
            session["email"] = email
            return redirect(url_for("dashboard"))
        error = "Sai tài khoản hoặc mật khẩu"
    return render_template("login.html", error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        email   = request.form.get("email")
        pw      = request.form.get("password")
        confirm = request.form.get("confirm")
        if pw != confirm:
            error = "Mật khẩu không khớp"
        elif email in users:
            error = "Email đã tồn tại"
        else:
            users[email] = pw
            return redirect(url_for("login"))
    return render_template("register.html", error=error)

@app.route("/dashboard")
def dashboard():
    if "email" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

@app.route("/setting", methods=["GET", "POST"])
def setting():
    if "email" not in session:
        return redirect(url_for("login"))
    message = None
    if request.method == "POST":
        try:
            t_system_settings["threshold"]  = int(request.form.get("threshold", 2500))
            t_system_settings["alert_email"] = request.form.get("alert_email", "")
            message = "Đã lưu cấu hình thành công"
        except:
            message = "Lỗi: không thể lưu cấu hình"
    return render_template("setting.html", message=message, settings=t_system_settings)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    # Start MQTT loop
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()

    # Run Flask
    app.run(host="0.0.0.0", port=5000, debug=True)
