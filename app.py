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
# Load Firebase credentials and initialize Admin SDK with correct project URL
cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://tutrungtamba-default-rtdb.firebaseio.com"
})

# Function to push sensor data directly to database root with keys based on sid
def send_realtime_firebase(sid, addr, temp, hum, gas, fire):
    root_ref = db.reference('/')
    timestamp = datetime.datetime.utcnow().isoformat()
    payload = {
        f"{sid}_address": addr,
        f"{sid}_temp":      temp,
        f"{sid}_humi":      hum,
        f"{sid}_mq2":       gas,
        f"{sid}_fire":      fire,
        f"{sid}_updated":   timestamp
    }
    # Use update to write multiple keys at root without overwriting all data
    root_ref.update(payload)
    print(f"[{sid}] Updated keys {list(payload.keys())} @ {timestamp}")

# Serial SIM module configuration (if any)
try:
    sim_serial = serial.Serial("COM7", 9600, timeout=1)
except serial.SerialException:
    sim_serial = None

phone_number = "+849xxxxxxxx"

# MQTT settings
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT   = 1883
MQTT_TOPICS = [("datasensor1", 0), ("datasensor2", 0), ("datasensor3", 0)]

# In-memory stores
users = {"anh066214@gmail.com": "123456"}
t_system_settings = {"threshold": 2500, "alert_email": ""}

# Function to send SMS via SIM module
def send_sms(content):
    if sim_serial and sim_serial.is_open:
        try:
            sim_serial.write(b'AT\r'); time.sleep(0.5)
            sim_serial.write(b'AT+CMGF=1\r'); time.sleep(0.5)
            sim_serial.write(f'AT+CMGS="{phone_number}"\r'.encode()); time.sleep(0.5)
            sim_serial.write(content.encode() + b'\x1A'); time.sleep(2)
            print("SMS sent:", content)
        except Exception as e:
            print("SMS error:", e)
    else:
        print("SIM module not available.")

# MQTT callbacks

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker, rc=", rc)
    for topic, qos in MQTT_TOPICS:
        client.subscribe(topic, qos)


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        sid, addr, temp, hum, gas, fire = payload.split(',')
        temp = float(temp)
        hum  = float(hum)
        gas  = float(gas)
        fire = int(fire)
    except Exception as e:
        print("MQTT parse error:", e, msg.payload)
        return

    send_realtime_firebase(sid, addr, temp, hum, gas, fire)
    if fire == 1 or gas >= t_system_settings.get("threshold", 2500):
        send_sms(f"ALERT: Node {sid} at {addr} - gas={gas}, fire={fire}")

# Flask app setup
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_me")
CORS(app)

@app.route("/")
def index():
    return redirect(url_for('login'))

@app.route("/login", methods=["GET","POST"])
def login():
    error=None
    if request.method=="POST":
        e=request.form['email']; p=request.form['password']
        if e in users and users[e]==p:
            session['email']=e
            return redirect(url_for('dashboard'))
        error="Sai tài khoản hoặc mật khẩu"
    return render_template('login.html', error=error)

@app.route("/register", methods=["GET","POST"])
def register():
    error=None
    if request.method=="POST":
        e=request.form['email']; p=request.form['password']; c=request.form['confirm']
        if p!=c: error="Mật khẩu không khớp"
        elif e in users: error="Email đã tồn tại"
        else:
            users[e]=p
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

@app.route("/dashboard")
def dashboard():
    if 'email' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route("/setting", methods=["GET","POST"])
def setting():
    if 'email' not in session: return redirect(url_for('login'))
    message=None
    if request.method=='POST':
        try:
            t_system_settings['threshold']=int(request.form['threshold'])
            t_system_settings['alert_email']=request.form['alert_email']
            message="Lưu cấu hình thành công"
        except:
            message="Lỗi lưu cấu hình"
    return render_template('setting.html',message=message,settings=t_system_settings)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__=="__main__":
    client=mqtt.Client()
    client.on_connect=on_connect
    client.on_message=on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    app.run(host="0.0.0.0", port=5000, debug=True)
