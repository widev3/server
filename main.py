import sys

sys.dont_write_bytecode = True

from endpoints.mount import mount_bp
from endpoints.session import session_bp
from classes.DeviceInfo import DeviceInfo
from flask import Flask, request, jsonify
from SessionProperties import SessionProperties as SP
from endpoints.hwcontroller import hwcontroller_bp

SP().DEVICE_ID = DeviceInfo.get_identifier()
SP().MOUNT = DeviceInfo.select_mount()

app = Flask(__name__)

app.register_blueprint(session_bp, url_prefix="/session")
app.register_blueprint(mount_bp, url_prefix="/mount")
app.register_blueprint(hwcontroller_bp, url_prefix="/hwcontroller")


@app.before_request
def app_before_request():
    token = request.headers.get("Authorization")
    if token and SP().SID and token != str(SP().SID):
        return jsonify({"error": "session already acquired"}), 401
    if token and not SP().SID:
        return jsonify({"error": "no active session"}), 401
    if not token and request.path != "/session/acquire":
        return jsonify({"error": "unauthorized"}), 401


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="56361", debug=True)
