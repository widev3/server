#!/usr/bin/env python3
import socket
import threading
import time
from flask import Flask, request, jsonify, render_template_string
from adafruit_pca9685 import PCA9685
from board import SCL, SDA
import busio

#Flask
#adafruit-circuitpython-pca9685
#adafruit-blinka

class W3Mount:
    def __init__(self, freq_hz=50, channels=[0, 1], host="0.0.0.0", port=5000):
        # =============================
        # Configurazione base
        # =============================
        self.FREQUENCY_HZ = freq_hz
        self.PERIOD_US = 1_000_000 / freq_hz
        self.CHANNELS = channels
        self.HOST = host
        self.PORT = port
        self.app = Flask(__name__)
        self.pca = None
        self.running = False

        # =============================
        # Inizializza PCA9685
        # =============================
        try:
            i2c = busio.I2C(SCL, SDA)
            self.pca = PCA9685(i2c)
            self.pca.frequency = self.FREQUENCY_HZ
            print("PCA9685 initialized.")
        except Exception as e:
            print("Error during PCA9685 initialization:", e)

        # Registra le rotte API
        self.register_routes()

    # ====================================================
    # 🔹 Utility
    # ====================================================
    def move_servo(self, channel, angle):
        """Moves a servo with linear conversion 0–180°"""
        try:
            if self.pca is None:
                return False, "PCA9685 not initialized"

            # ✅ Range corretto per RDS51160
            pulse_min, pulse_max = 500, 2500  # µs
            pulse_us = pulse_min + (pulse_max - pulse_min) * (angle / 180)
            duty = int(pulse_us / self.PERIOD_US * 65535)
            self.pca.channels[channel].duty_cycle = duty
            print(f"[SERVO {channel}] → {angle:.2f}° ({pulse_us:.1f} µs)")
            return True, None
        except Exception as e:
            return False, str(e)

    # ====================================================
    # 🔹 ENDPOINTS API
    # ====================================================
    def register_routes(self):
        app = self.app

        @app.route("/")
        def index():
            try:
                return render_template_string(self.html_interface())
            except Exception as e:
                return f"Interface Error: {e}", 500

        @app.route("/ping")
        def ping():
            try:
                return jsonify({"ok": True, "message": "Pong"})
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)}), 500

        @app.route("/move", methods=["GET", "POST"])
        def move():
            try:
                ch = int(request.args.get("ch", request.form.get("ch")))
                angle = float(request.args.get("angle", request.form.get("angle")))
                ok, err = self.move_servo(ch, angle)
                if not ok:
                    return jsonify({"ok": False, "error": err}), 400
                return jsonify({"ok": True, "ch": ch, "angle": angle})
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)}), 400

        @app.route("/move/abs", methods=["POST"])
        def move_abs():
            try:
                ch = int(request.args.get("ch"))
                pulse = float(request.args.get("pulse"))
                duty = int(pulse / self.PERIOD_US * 65535)
                self.pca.channels[ch].duty_cycle = duty
                print(f"[SERVO {ch}] → direct impulse {pulse} µs")
                return jsonify({"ok": True, "ch": ch, "pulse": pulse})
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)}), 400

        @app.route("/move/test", methods=["POST"])
        def move_test():
            try:
                for angle in range(0, 181, 30):
                    for ch in self.CHANNELS:
                        self.move_servo(ch, angle)
                    time.sleep(0.5)
                return jsonify({"ok": True, "message": "Test completed"})
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)}), 400

        @app.route("/stop", methods=["POST"])
        def stop():
            try:
                for ch in self.CHANNELS:
                    self.pca.channels[ch].duty_cycle = 0
                print("Servos stopped.")
                return jsonify({"ok": True, "message": "Servos stopped"})
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)}), 400

        @app.route("/channels")
        def channels():
            try:
                return jsonify({"ok": True, "channels": self.CHANNELS})
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)}), 500

        @app.route("/setfreq", methods=["POST"])
        def setfreq():
            try:
                freq = int(request.args.get("freq"))
                self.pca.frequency = freq
                print(f"PWM frequency set to {freq} Hz")
                return jsonify({"ok": True, "freq": freq})
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)}), 400

        @app.route("/info")
        def info():
            try:
                host = socket.gethostname()
                ip = socket.gethostbyname(host)
                return jsonify({
                    "ok": True,
                    "device": host,
                    "ip": ip,
                    "frequency": self.FREQUENCY_HZ,
                    "channels": self.CHANNELS
                })
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)}), 500

        @app.route("/exec", methods=["POST"])
        def exec_cmd():
            try:
                cmd = request.args.get("cmd")
                if cmd == "reset":
                    for ch in self.CHANNELS:
                        self.pca.channels[ch].duty_cycle = 0
                    print("Reset executed.")
                    return jsonify({"ok": True, "message": "Reset executed"})
                return jsonify({"ok": False, "error": "Unknown command"})
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)}), 400

    # ====================================================
    # 🖥️ INTERFACCIA HTML BASE
    # ====================================================
    def html_interface(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
          <title>W3Mount Servo Control</title>
          <style>
            body { font-family: sans-serif; background:#111; color:#eee; text-align:center; margin-top:40px; }
            h1 { color:#6cf; }
            input[type=range] { width: 400px; }
            .servo { margin: 30px; }
          </style>
        </head>
        <body>
          <h1>Servo RDS51160 Control</h1>
          <div class="servo">
            <label>Servo 1</label><br>
            <input type="range" id="servo0" min="0" max="180" value="90" oninput="send(0,this.value)">
            <span id="val0">90°</span>
          </div>
          <div class="servo">
            <label>Servo 2</label><br>
            <input type="range" id="servo1" min="0" max="180" value="90" oninput="send(1,this.value)">
            <span id="val1">90°</span>
          </div>
          <script>
            async function send(ch,val){
              document.getElementById("val"+ch).innerText = val + "°";
              await fetch(`/move?ch=${ch}&angle=${val}`);
            }
          </script>
        </body>
        </html>
        """

    # ====================================================
    # 🚀 AVVIO SERVER
    # ====================================================
    def run_server(self):
        thread = threading.Thread(target=self.app.run, kwargs={
            "host": self.HOST,
            "port": self.PORT
        })
        thread.daemon = True
        thread.start()
        print(f"Server started on http://{self.HOST}:{self.PORT}")


# ====================================================
# Avvio diretto
# ====================================================
if __name__ == "__main__":
    mount = W3Mount()
    mount.run_server()
    while True:
        time.sleep(1)
