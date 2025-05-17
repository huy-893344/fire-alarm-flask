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
# Paste your entire JSON service account key below, preserving line breaks
service_account_info = {
    "type": "service_account",
    "project_id": "pham-quoc-anh-default-rtdb",
    "private_key_id": "YOUR_PRIVATE_KEY_ID",
    "private_key": """
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BA... (your key here) ...
-----END PRIVATE KEY-----
""",
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
    print(f"[{sid}] Pushed @{payload['timestamp']}")

try:
    sim_serial = serial.Serial("COM7", 9600, timeout=1)
except serial.SerialException:
    sim_serial = None
phone_number = "+849xxxxxxxx"
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT   = 1883
MQTT_TOPICS = [("datasensor1",0),("datasensor2",0),("datasensor3",0)]


def on_connect(client, userdata, flags, rc):
    for topic,qos in MQTT_TOPICS:
        client.subscribe(topic,qos)

def on_message(client, userdata, msg):
    try:
        sid, addr, t, h, g, f = msg.payload.decode().split(',')
        t,h,g,f = float(t),float(h),float(g),int(f)
    except Exception as e:
        print("MQTT parse error:", e)
        return
    send_realtime_firebase(sid, addr, t, h, g, f)
    if f==1 or g>=t_system_settings.get('threshold',2500):
        send_sms(f"ALERT Node {sid}@{addr} gas={g}, fire={f}")

def send_sms(content):
    if sim_serial and sim_serial.is_open:
        sim_serial.write(b'AT\r'); time.sleep(0.5)
        sim_serial.write(b'AT+CMGF=1\r'); time.sleep(0.5)
        sim_serial.write(f'AT+CMGS="{phone_number}"\r'.encode()); time.sleep(0.5)
        sim_serial.write(content.encode()+b'\x1A'); time.sleep(2)
    else:
        print("SIM unavailable")

users={"anh@gmail.com":"123456"}
t_system_settings={"threshold":2500,"alert_email":""}

# ========== Flask App ==========
app=Flask(__name__)
app.secret_key=os.environ.get('SECRET_KEY','change_me')
CORS(app)

@app.route('/')
def index(): return redirect(url_for('login'))

@app.route('/login',methods=['GET','POST'])
def login():
    err=None
    if request.method=='POST':
        e,p = request.form['email'],request.form['password']
        if users.get(e)==p:
            session['email']=e; return redirect(url_for('dashboard'))
        err="Sai tài khoản"
    return render_template('login.html',error=err)

@app.route('/dashboard')
def dashboard():
    if 'email' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

@app.route('/api/realtime')
def api_realtime():
    return jsonify(db.reference('DataSensorRealTime').get() or {})

@app.route('/stream')
def stream():
    def evt():
        prev=None
        while True:
            curr=db.reference('DataSensorRealTime').get() or {}
            if curr!=prev: yield f"data: {json.dumps(curr)}\n\n"; prev=curr
            time.sleep(3)
    return Response(evt(),mimetype='text/event-stream')

if __name__=='__main__':
    client=mqtt.Client(); client.on_connect=on_connect; client.on_message=on_message
    client.connect(MQTT_BROKER, MQTT_PORT,60); client.loop_start()
    app.run(host='0.0.0.0',port=5000,debug=True)
