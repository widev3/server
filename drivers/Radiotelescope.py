import math
import smbus2
import numpy as np
import drivers.is_rpi
from time import sleep

if drivers.is_rpi.is_rpi():
    import RPi.GPIO as GPIO

from astropy import units
from gpiozero import PWMLED
from astropy.time import Time
from datetime import datetime
from datetime import timezone
from classes.Mount import Mount
from gpiozero import RotaryEncoder
from astropy.coordinates import AltAz
from astropy.coordinates import SkyCoord
from astropy.coordinates import EarthLocation
from drivers.TonalBuzzerDevice import TonalBuzzerDevice as TBD


class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialized = True

        if drivers.is_rpi.is_rpi():
            self.MPU6050_ADDR = 0x68
            self.PWR_MGMT_1 = 0x6B
            self.ACCEL_XOUT_H = 0x3B
            self.GYRO_XOUT_H = 0x43
            self.mpu6050_bus = None

            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            # azimuth motor
            self.ENA = 18
            self.IN1 = 23
            self.IN2 = 24
            self.pwm_a = PWMLED(self.ENA)
            GPIO.setup(self.IN1, GPIO.OUT)
            GPIO.setup(self.IN2, GPIO.OUT)

            # altitude motor
            self.ENB = 12
            self.IN3 = 8
            self.IN4 = 25
            self.pwm_b = PWMLED(self.ENB)
            GPIO.setup(self.IN3, GPIO.OUT)
            GPIO.setup(self.IN4, GPIO.OUT)

            # encoder
            self.PINA = 14
            self.PINB = 15
            self.rotary_encoder = RotaryEncoder(
                a=self.PINA,
                b=self.PINB,
                wrap=True,
                max_steps=360,
            )


class Radiotelescope(Mount):
    def __init__(self):
        self.__location = None
        self.__target = None  # it is always in icrs
        self.__offset = None  # it is always in icrs
        self.__behavior = None
        self.__running = False

    def __now_utc(self):
        return Time(datetime.now(timezone.utc))

    def __linear_path(self, start: SkyCoord, end: SkyCoord) -> SkyCoord:
        ra_vals = np.arange(start.ra.deg, end.ra.deg, 0.2)
        dec_vals = np.arange(start.dec.deg, end.dec.deg, 0.2)
        ints = int((len(ra_vals) ** 2 + len(dec_vals) ** 2) ** 0.5 + 1)
        ra_vals = np.linspace(start.ra.deg, end.ra.deg, ints) * units.deg
        dec_vals = np.linspace(start.dec.deg, end.dec.deg, ints) * units.deg
        return SkyCoord(ra=ra_vals, dec=dec_vals, frame=start.frame)

    def __mpu6050_data(self) -> tuple[float, float, float] | None:
        def start_restart():
            bus = smbus2.SMBus(1)
            bus.write_byte_data(Singleton().MPU6050_ADDR, Singleton().PWR_MGMT_1, 0)
            return bus

        def raw_data(bus, addr):
            high = bus.read_byte_data(Singleton().MPU6050_ADDR, addr)
            low = bus.read_byte_data(Singleton().MPU6050_ADDR, addr + 1)
            value = (high << 8) | low
            if value > 32767:
                value -= 65536
            return value

        if not Singleton().mpu6050_bus:
            Singleton().mpu6050_bus = start_restart()
        try:
            accel_x = raw_data(Singleton().mpu6050_bus, Singleton().ACCEL_XOUT_H)
            accel_y = raw_data(Singleton().mpu6050_bus, Singleton().ACCEL_XOUT_H + 2)
            accel_z = raw_data(Singleton().mpu6050_bus, Singleton().ACCEL_XOUT_H + 4)
            accel_x /= 16384.0 / 9.81
            accel_y /= 16384.0 / 9.81
            accel_z /= 16384.0 / 9.81

            a = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2)
            if a == 0:
                return None

            thetaX = math.degrees(math.acos(accel_x / a))
            thetaY = math.degrees(math.acos(accel_y / a))
            thetaZ = math.degrees(math.acos(accel_z / a))
            return thetaX, thetaY, thetaZ
        except:
            Singleton().mpu6050_bus = None
            self.__mpu6050_data()

    def __get_az(self) -> float:
        return Singleton().rotary_encoder.steps if drivers.is_rpi.is_rpi() else None

    def __get_alt(self) -> float:
        return self.__mpu6050_data()[0] if drivers.is_rpi.is_rpi() else None

    def __run(self, az: float, alt: float) -> None:
        def forward_azimuth(speed):
            if drivers.is_rpi.is_rpi():
                GPIO.output(Singleton().IN1, GPIO.HIGH)
                GPIO.output(Singleton().IN2, GPIO.LOW)
                Singleton().pwm_a.value = speed

        def backward_azimuth(speed):
            if drivers.is_rpi.is_rpi():
                GPIO.output(Singleton().IN1, GPIO.LOW)
                GPIO.output(Singleton().IN2, GPIO.HIGH)
                Singleton().pwm_a.value = speed

        def forward_altitude(speed):
            if drivers.is_rpi.is_rpi():
                GPIO.output(Singleton().IN3, GPIO.HIGH)
                GPIO.output(Singleton().IN4, GPIO.LOW)
                Singleton().pwm_b.value = speed

        def backward_altitude(speed):
            if drivers.is_rpi.is_rpi():
                GPIO.output(Singleton().IN3, GPIO.LOW)
                GPIO.output(Singleton().IN4, GPIO.HIGH)
                Singleton().pwm_b.value = speed

        def stop_azimuth():
            if drivers.is_rpi.is_rpi():
                GPIO.output(Singleton().IN1, GPIO.LOW)
                GPIO.output(Singleton().IN2, GPIO.LOW)
                Singleton().pwm_a.value = 0

        def stop_altitude():
            if drivers.is_rpi.is_rpi():
                GPIO.output(Singleton().IN3, GPIO.LOW)
                GPIO.output(Singleton().IN4, GPIO.LOW)
                Singleton().pwm_b.value = 0

        az_real = self.__get_az()
        alt_real = self.__get_alt()
        print(f"Target {az:05f}, {alt:05f}", end="\t")
        print(f"Position {az_real:05f}. {alt_real:05f}", end="\t")
        ang_res = 5

        if az > az_real + ang_res:
            forward_azimuth(1)
            print("→", end=" ")
        elif az < az_real - ang_res:
            backward_azimuth(1)
            print("←", end=" ")
        else:
            stop_azimuth()
            print("↔", end=" ")

        if alt > alt_real + ang_res:
            forward_altitude(1)
            print("↑")
        elif alt < alt_real - ang_res:
            backward_altitude(1)
            print("↓")
        else:
            stop_altitude()
            print("↕")

    def get_location(self):
        return self.__location

    def get_target(self):
        return self.__target

    def get_offset(self):
        return self.__offset

    def get_position(self):
        return (self.__get_alt(), self.__get_az())

    def get_behavior(self):
        return self.__behavior

    def get_running(self):
        return self.__running

    def set_location(self, location: EarthLocation):
        self.__location = location

    def set_target(self, alt=None, az=None, ra=None, dec=None) -> None:
        if alt is not None and az is not None:
            altaz_frame = AltAz(obstime=self.__now_utc(), location=self.__location)
            altaz_coords = SkyCoord(alt=alt, az=az, frame=altaz_frame)
            self.__target = altaz_coords.transform_to("icrs")
        elif ra is not None and dec is not None:
            self.__target = SkyCoord(ra=ra, dec=dec, frame="icrs")

    def set_absolute_offset(self, alt=None, az=None, ra=None, dec=None) -> None:
        if alt is not None or az is not None:
            altaz_frame = AltAz(obstime=self.__now_utc(), location=self.__location)
            altaz_coords = self.__target.transform_to(altaz_frame)
            altaz_coords = SkyCoord(
                alt=alt if alt is not None else altaz_coords.alt,
                az=az if az is not None else altaz_coords.az,
                frame=altaz_frame,
            )
            self.__offset = altaz_coords.transform_to("icrs")
        elif ra is not None or dec is not None:
            self.__offset = SkyCoord(
                ra=ra if ra is not None else self.__target.ra,
                dec=dec if dec is not None else self.__target.dec,
                frame="icrs",
            )

    def set_relative_offset(self, alt=None, az=None, ra=None, dec=None) -> None:
        if alt is not None or az is not None:
            altaz_frame = AltAz(obstime=self.__now_utc(), location=self.__location)
            altaz_coords = self.__target.transform_to(altaz_frame)
            altaz_coords = SkyCoord(
                alt=altaz_coords.alt - alt if alt is not None else altaz_coords.alt,
                az=altaz_coords.az - az if az is not None else altaz_coords.az,
                frame=altaz_frame,
            )
            self.__offset = altaz_coords.transform_to("icrs")
        elif ra is not None or dec is not None:
            self.__offset = SkyCoord(
                ra=self.__target.ra - ra if ra is not None else self.__target.ra,
                dec=self.__target.dec - dec if dec is not None else self.__target.dec,
                frame="icrs",
            )

    def run(self, bh: str) -> None:
        self.__running = True
        if bh == "follow":
            while self.__running:
                sleep(1)
                altaz_frame = AltAz(obstime=self.__now_utc(), location=self.__location)
                altaz_coords = self.__target.transform_to(altaz_frame)
                self.__run(altaz_coords.az.deg, altaz_coords.alt.deg)
        elif bh == "transit":
            altaz_frame = AltAz(obstime=self.__now_utc(), location=self.__location)
            altaz_coords = self.__target.transform_to(altaz_frame)
            self.__run(altaz_coords.az.deg, altaz_coords.alt.deg)
            TBD().write(
                [
                    # Measure 1
                    ("C4", 0.25),
                    ("E4", 0.25),
                    ("G4", 0.25),
                    ("C5", 0.25),
                    # Measure 2
                    ("B4", 0.25),
                    ("A4", 0.25),
                    ("G4", 0.5),
                    # Measure 3
                    ("E4", 0.25),
                    ("F4", 0.25),
                    ("G4", 0.25),
                    (None, 0.25),
                    # Measure 4
                    ("C5", 0.5),
                    ("B4", 0.25),
                    ("A4", 0.25),
                    # # Measure 5
                    ("G4", 0.25),
                    ("A4", 0.25),
                    ("B4", 0.25),
                    ("D5", 0.25),
                    # Measure 6
                    ("C5", 0.5),
                ]
            )
        elif bh == "route":
            path_coords = self.__linear_path(start=self.__offset, end=self.__target)
            for path_coord in path_coords:
                sleep(5)
                altaz_frame = AltAz(obstime=self.__now_utc(), location=self.__location)
                altaz_coords = path_coord.transform_to(altaz_frame)
                self.__run(altaz_coords.az.deg, altaz_coords.alt.deg)
                TBD().write(
                    [
                        # Measure 1
                        ("C4", 0.25),
                        ("E4", 0.25),
                        ("G4", 0.25),
                        ("C5", 0.25),
                        # Measure 2
                        ("B4", 0.25),
                        ("A4", 0.25),
                        ("G4", 0.5),
                        # Measure 3
                        ("E4", 0.25),
                        ("F4", 0.25),
                        ("G4", 0.25),
                        (None, 0.25),
                        # Measure 4
                        ("C5", 0.5),
                        ("B4", 0.25),
                        ("A4", 0.25),
                        # # Measure 5
                        ("G4", 0.25),
                        ("A4", 0.25),
                        ("B4", 0.25),
                        ("D5", 0.25),
                        # Measure 6
                        ("C5", 0.5),
                    ]
                )

        self.__running = False
        print("Done run")

    def stop(self) -> None:
        self.__running = False
