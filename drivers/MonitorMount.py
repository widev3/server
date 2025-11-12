import time
import socket
import threading
import drivers.is_rpi
from classes.Mount import Mount

#  Hardware Detect (Raspberry Pi o Mock mode)
if drivers.is_rpi.is_rpi():
    import RPi.GPIO as GPIO
    from adafruit_pca9685 import PCA9685
    from board import SCL, SDA
    import busio

#  Singleton PCA9685 — one istance / session
class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.pca = None

        if drivers.is_rpi.is_rpi():
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                i2c = busio.I2C(SCL, SDA)
                self.pca = PCA9685(i2c)
                self.pca.frequency = 100
                print("[Singleton] PCA9685 initialized @100Hz")
            except Exception as e:
                print("[Singleton] Error initializing PCA9685:", e)
        else:
            print("[Singleton] Mock mode (non-Raspberry environment).")


# MonitorMount (implementazione di Mount)
class MonitorMount(Mount):
    def __init__(self):
        super().__init__()

        self.FREQUENCY_HZ = 100
        self.PERIOD_US = 1_000_000 / self.FREQUENCY_HZ
        self.CHANNELS = [0, 1]
        self.__running = False

        # Hardware Singleton
        self.hw = Singleton()
        self.pca = self.hw.pca

        if self.pca:
            print("[MonitorMount] PCA9685 ready.")
        else:
            print("[MonitorMount] PCA9685 unavailable (mock mode).")

    #  Servo Control
    def move_servo(self, channel, angle):
        """Moves a servo with linear conversion 0–180°"""
        try:
            if self.pca is None:
                return False, "PCA9685 not initialized"

            pulse_min, pulse_max = 500, 2500  # microseconds
            pulse_us = pulse_min + (pulse_max - pulse_min) * (angle / 180.0)
            duty = int(pulse_us / self.PERIOD_US * 65535)
            self.pca.channels[channel].duty_cycle = duty
            print(f"[SERVO {channel}] → {angle:.2f}° ({pulse_us:.0f} µs)")
            self.__running = True
            return True, None
        except Exception as e:
            return False, str(e)

    def move_absolute(self, channel, pulse):
        """Moves servo directly using pulse width (µs)"""
        try:
            if not self.pca:
                return False, "PCA9685 not initialized"
            duty = int(pulse / self.PERIOD_US * 65535)
            self.pca.channels[channel].duty_cycle = duty
            print(f"[SERVO {channel}] direct impulse {pulse} µs")
            self.__running = True
            return True, None
        except Exception as e:
            return False, str(e)

    def stop(self):
        """Stops all servos"""
        try:
            if self.pca:
                for ch in self.CHANNELS:
                    self.pca.channels[ch].duty_cycle = 0
            self.__running = False
            print("[MonitorMount] Servos stopped.")
        except Exception as e:
            print("[MonitorMount] Error stopping servos:", e)

    def set_frequency(self, freq):
        """Changes PWM frequency"""
        try:
            if self.pca:
                self.pca.frequency = freq
                self.FREQUENCY_HZ = freq
                self.PERIOD_US = 1_000_000 / freq
                print(f"[MonitorMount] PWM frequency set to {freq} Hz")
            return True, None
        except Exception as e:
            return False, str(e)

    #  Status and Info
    def get_position(self):
        """Returns current PWM duty (simulated position)"""
        if not self.pca:
            return None
        try:
            positions = {ch: self.pca.channels[ch].duty_cycle for ch in self.CHANNELS}
            return positions
        except Exception as e:
            print("[MonitorMount] Error reading servo positions:", e)
            return None

    def get_running(self):
        """Returns True if running"""
        return self.__running

    def get_info(self):
        """Returns device and PCA9685 info"""
        try:
            host = socket.gethostname()
            ip = socket.gethostbyname(host)
            return {
                "device": host,
                "ip": ip,
                "frequency": self.FREQUENCY_HZ,
                "channels": self.CHANNELS,
                "pca_initialized": self.pca is not None,
            }
        except Exception as e:
            return {"error": str(e)}

    #  HTML Web Interface (manual control)
    def html_interface(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
          <title>MonitorMount Servo Control</title>
          <style>
            body { font-family:sans-serif; background:#111; color:#eee; text-align:center; margin-top:40px; }
            h1 { color:#6cf; }
            input[type=range] { width:400px; }
            .servo { margin:30px; }
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
              await fetch(`/hardware/move?ch=${ch}&angle=${val}`);
            }
          </script>
        </body>
        </html>
        """

    #  Implementations for Mount (abstract)
    def set_location(self, location):
        """Imposta la posizione geografica simulata"""
        self._location = location
        print(f"[MonitorMount] Location set: {location}")

    def get_location(self):
        """Ritorna la posizione impostata"""
        return getattr(self, "_location", None)

    def set_target(self, alt=None, az=None, ra=None, dec=None):
        """Imposta il target"""
        self._target = {"alt": alt, "az": az, "ra": ra, "dec": dec}
        print(f"[MonitorMount] Target set: {self._target}")

    def get_target(self):
        """Ritorna il target corrente"""
        return getattr(self, "_target", None)

    def set_absolute_offset(self, alt=None, az=None, ra=None, dec=None):
        """Offset assoluto"""
        self._abs_offset = {"alt": alt, "az": az, "ra": ra, "dec": dec}
        print(f"[MonitorMount] Absolute offset set: {self._abs_offset}")

    def set_relative_offset(self, alt=None, az=None, ra=None, dec=None):
        """Offset relativo"""
        self._rel_offset = {"alt": alt, "az": az, "ra": ra, "dec": dec}
        print(f"[MonitorMount] Relative offset set: {self._rel_offset}")

    def get_offset(self):
        """Ritorna offset attuale"""
        return getattr(self, "_rel_offset", None) or getattr(self, "_abs_offset", None)

    def get_behavior(self):
        """Comportamento corrente (follow, route...)"""
        return getattr(self, "_behavior", None)

    def run(self, bh: str):
        """Simula un comportamento"""
        self._behavior = bh
        self.__running = True
        print(f"[MonitorMount] Run started (behavior='{bh}')")

        # Simulazione movimento 2 secondi
        time.sleep(2)

        self.__running = False
        print(f"[MonitorMount] Run finished (behavior='{bh}')")
