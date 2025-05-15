from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import serial
import time

app = Flask(__name__)
app.secret_key = "your_secret_key"
socketio = SocketIO(app, async_mode="eventlet")

# ================= MQTT Config =================
mqtt_broker = "localhost"
mqtt_port = 1883
mqtt_topics = ["datasensor1", "datasensor2", "datasensor3"]  # hỗ trợ nhiều node

# ================= SIM Module Serial Config =================
try:
    sim_serial = serial.Serial("COM7", 9600, timeout=1)
except:
    sim_serial = None  # fallback nếu không kết nối được

phone_number = "+849xxxxxxxx"  # Số điện thoại nhận cảnh báo

# =============== Dummy User ===============
users = {
    "anh066214@gmail.com": "123456"
}

# =============== Settings (in-memory) ===============
system_settings = {
    "threshold": 2500,
    "alert_email": ""
}

# ================= Flask Routes =================
@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if email in users and users[email] == password:
            session["email"] = email
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Sai tài khoản hoặc mật khẩu")
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "email" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")


@app.route("/logout")
def logout():
    session.pop("email", None)
    return redirect(url_for("login"))


@app.route("/setting", methods=["GET", "POST"])
def setting():
    if "email" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        try:
            system_settings["threshold"] = int(request.form.get("threshold", 2500))
            system_settings["alert_email"] = request.form.get("alert_email", "")
            return render_template("setting.html", success="Đã lưu cấu hình thành công")
        except Exception as e:
            return render_template("setting.html", success="Lỗi: không thể lưu cấu hình")
    return render_template("setting.html")
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Bạn có thể mở rộng thêm kiểm tra email đã tồn tại hay chưa
        email = request.form.get["email"]
        password = request.form.get["password"]
        confirm = request.form.get["confirm"]
        if password != confirm:
            return render_template("register.html", error="Mật khẩu không khớp")
        users[email] = password
        return redirect(url_for("login"))
    return render_template("register.html")


# ================= MQTT CALLBACK =================
def on_connect(client, userdata, flags, rc):
    print("MQTT connected")
    for topic in mqtt_topics:
        client.subscribe(topic)


def on_message(client, userdata, msg):
    try:
        data = msg.payload.decode().split(",")
        address = data[0]
        temp = float(data[1])
        hum = float(data[2])
        gas = float(data[3])
        fire = int(data[4])

        print(f"Data from {msg.topic}: Addr={address}, Temp={temp}, Hum={hum}, Gas={gas}, Fire={fire}")

        node = msg.topic.replace("datasensor", "")
        socketio.emit(f"update_data_sensor{node}", {
            "address": address,
            "temperature": temp,
            "humidity": hum,
            "mq2": gas,
            "fire": fire
        })

        if fire == 1 or gas >= system_settings["threshold"]:
            send_sms(f"CẢNH BÁO: Cháy/gas tại {address} (Node {node})! MQ2={gas}ppm")

    except Exception as e:
        print("MQTT error:", e)


# ================= GỬI SMS =================
def send_sms(content):
    try:
        if sim_serial and sim_serial.is_open:
            sim_serial.write(b'AT\r')
            time.sleep(0.5)
            sim_serial.write(b'AT+CMGF=1\r')
            time.sleep(0.5)
            sim_serial.write(f'AT+CMGS="{phone_number}"\r'.encode())
            time.sleep(0.5)
            sim_serial.write(content.encode() + b"\x1A")  # Ctrl+Z
            time.sleep(2)
            print("Đã gửi SMS:", content)
        else:
            print("SIM module not available.")
    except Exception as e:
        print("Lỗi gửi SMS:", e)


# ================= START MQTT =================
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(mqtt_broker, mqtt_port, 60)
mqtt_client.loop_start()

# ================= MAIN =================
if __name__ == "__main__":
    socketio.run(app, debug=True)
