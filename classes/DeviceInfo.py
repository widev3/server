import re
import subprocess
from drivers.Monitor import Monitor
from SessionProperties import SessionProperties as SP
from drivers.Radiotelescope import Radiotelescope


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
        match_model = re.search(r"Pi\s*([0-9]+)", model_raw)
        pi_number = match_model.group(1) if match_model else "X"
        match_rev = re.search(r"Rev\s*([0-9\.]+)", model_raw)
        revision = match_rev.group(1) if match_rev else "X"

        return f"Pi{pi_number}", revision

    @staticmethod
    def get_identifier():
        serial = DeviceInfo.get_serial()
        raw = DeviceInfo.get_model_raw()

        pi_model, pi_rev = DeviceInfo.parse_model(raw)

        return f"{serial}_{pi_model}_{pi_rev}"

    @staticmethod
    def select_mount():
        if not SP().DEVICE_ID or "_" not in SP().DEVICE_ID:
            return Radiotelescope()  # fallback

        parts = SP().DEVICE_ID.split("_")
        model = parts[1]

        if model in ["Pi4", "Pi5"]:
            return Radiotelescope()

        if model in ["Pi3", "Pi02", "Pi0"]:
            return Monitor()

        return Radiotelescope()
