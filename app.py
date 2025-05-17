#!/usr/bin/env python3
# app.py

import os
import json
import datetime
import time
import firebase_admin
from firebase_admin import credentials, db
import paho.mqtt.client as mqtt
import serial
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
from flask_cors import CORS

# ========== FIREBASE CONFIGURATION (Embed service account info directly) ==========
# Replace placeholder values with your actual Firebase service account details
service_account_info = {
    "type": "service_account",
    "project_id": "pham-quoc-anh-default-rtdb",
    "private_key_id": "YOUR_PRIVATE_KEY_ID",
    "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
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
# Function to push sensor data to RTDB under DataSensorRealTime/{sid}
def send_realtime_firebase(sid, addr, temp, hum, gas, fire):
    ref = db.reference('DataSensorRealTime')
    payload = {
        "send_address": addr,
        "temperature":   temp,
        "humidity":      hum,
        "mq2":           gas,
        "fire":          fire,
        "timestamp":     datetime.datetime.utcnow().isoformat()
    }
    ref.child(sid).set(payload)
    print(f"[{sid}] Pushed to DataSensorRealTime/{sid} @ {payload['timestamp']}")

# Serial SIM module configuration (optional)
try:
    sim_serial = serial.Serial("COM7", 9600, timeout=1)
except serial.SerialException:
    sim_serial = None

phone_number = "+849xxxxxxxx"

# MQTT settings
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT   = 1883
MQTT_TOPICS = [("datasensor1", 0), ("datasensor2", 0), ("datasensor3", 0)]

def on_connect(client, userdata, flags, rc):
    print("MQTT connected with rc=", rc)
    for topic, qos in MQTT_TOPICS:
        client.subscribe(topic, qos)

def on_message(client, userdata, msg):
    try:
        sid, addr, temp, hum, gas, fire = msg.payload.decode().split(',')
        temp, hum, gas, fire = float(temp), float(hum), float(gas), int(fire)
    except Exception as e:
        print("Error parsing MQTT payload:", e)
        return
    send_realtime_firebase(sid, addr, temp, hum, gas, fire)
    # SMS alert if needed
    if fire == 1 or gas >= t_system_settings.get("threshold", 2500):
        send_sms(f"ALERT: Node {sid}@{addr} - gas={gas}, fire={fire}")

# Function to send SMS via SIM module (optional)
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
        print("SIM module not available")

# In-memory stores
users = {"anh066214@gmail.com": "123456"}
t_system_settings = {"threshold": 2500, "alert_email": ""}

# ========== Flask Application ==========
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_me")
CORS(app)

@app.route("/")
def index():
    return redirect(url_for('login'))

@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        pwd   = request.form.get('password')
        if email in users and users[email] == pwd:
            session['email'] = email
            return redirect(url_for('dashboard'))
        error = "Sai tài khoản hoặc mật khẩu"
    return render_template('login.html', error=error)

@app.route("/register", methods=["GET","POST"])
def register():
    error = None
    if request.method == 'POST':
        email, pwd, confirm = request.form.get('email'), request.form.get('password'), request.form.get('confirm')
        if pwd != confirm:
            error = "Mật khẩu không khớp"
        elif email in users:
            error = "Email đã tồn tại"
        else:
            users[email] = pwd
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

@app.route("/dashboard")
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route("/setting", methods=["GET","POST"])
def setting():
    if 'email' not in session:
        return redirect(url_for('login'))
    message = None
    if request.method == 'POST':
        try:
            t_system_settings['threshold']  = int(request.form.get('threshold', 2500))
            t_system_settings['alert_email'] = request.form.get('alert_email', '')
            message = "Lưu cấu hình thành công"
        except:
            message = "Lỗi lưu cấu hình"
    return render_template('setting.html', message=message, settings=t_system_settings)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/realtime')
def api_realtime():
    data = db.reference('DataSensorRealTime').get() or {}
    return jsonify(data)

@app.route('/stream')
def stream():
    def event_stream():
        prev = None
        while True:
            curr = db.reference('DataSensorRealTime').get() or {}
            if curr != prev:
                yield f"data: {json.dumps(curr)}\n\n"
                prev = curr
            time.sleep(3)
    return Response(event_stream(), mimetype='text/event-stream')

if __name__ == '__main__':
    # Start MQTT listener
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()

    # Run Flask server
    app.run(host='0.0.0.0', port=5000, debug=True)
