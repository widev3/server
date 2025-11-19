from drivers.MonitorMount import MonitorMount
from drivers.RadiotelescopeMount import RadiotelescopeMount

import subprocess
import re


class DeviceInfo:

    @staticmethod
    def get_serial():
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.startswith("Serial"):
                        return line.split(":")[1].strip()
        except:
            return "unknownserial"

    @staticmethod
    def get_model_raw():
        try:
            return (
                subprocess.check_output(["cat", "/proc/device-tree/model"])
                .decode()
                .strip()
            )
        except:
            return "unknown"

    @staticmethod
    def parse_model(model_raw: str):
        # Converts:         'Raspberry Pi 4 Model B Rev 1.4 in:'Pi4', '1.4'
        match_model = re.search(
            r"Pi\s*([0-9]+)", model_raw
        )  # Extract Raspberry Nr. (3, 4, 5, Zero ecc.)
        pi_number = match_model.group(1) if match_model else "X"

        match_rev = re.search(r"Rev\s*([0-9\.]+)", model_raw)  # Get revision
        revision = match_rev.group(1) if match_rev else "X"

        return f"Pi{pi_number}", revision

    @staticmethod
    def get_identifier():
        # Return a string in thr format: serial_PiX_revision - example: 10000000abcdef_Pi4_1.4
        serial = DeviceInfo.get_serial()
        raw = DeviceInfo.get_model_raw()

        pi_model, pi_rev = DeviceInfo.parse_model(raw)

        return f"{serial}_{pi_model}_{pi_rev}"

    @staticmethod
    def select_mount(device_id: str):
        # device_id example: 10000000abcd_Pi4_1.4

        if not device_id or "_" not in device_id:
            return RadiotelescopeMount()  # fallback

        # device_id (example: serial_Pi4_1.4)
        parts = device_id.split("_")
        model = parts[1]  # "Pi4"

        # logic - example [define]. It will read from online db where we can assign the real final mount type.
        if model in ["Pi4", "Pi5"]:
            return RadiotelescopeMount()

        if model in ["Pi3", "Pi02", "Pi0"]:
            return MonitorMount()

        # fallback
        return RadiotelescopeMount()
