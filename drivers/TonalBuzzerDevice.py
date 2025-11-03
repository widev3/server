import drivers.hw
from time import sleep
from gpiozero import TonalBuzzer
from classes.Device import Device


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

        if drivers.hw.is_rpi():
            TBPIN = 4
            self.tonal_buzzer = TonalBuzzer(TBPIN)


class TonalBuzzerDevice(Device):
    def __init__(self):
        pass

    def write(self, tune):
        if drivers.hw.is_rpi():
            for note, duration in tune:
                Singleton().tonal_buzzer.play(note)
                sleep(duration)
            Singleton().tonal_buzzer.stop()
