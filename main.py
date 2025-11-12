import sys

sys.dont_write_bytecode = True

from endpoints.mount import mount_bp
from endpoints.session import session_bp
#from endpoints.hardware import hardware_bp
from endpoints.hwcontroller import hwcontroller_bp
from SingletonSID import SingletonSID
from flask import Flask, request, jsonify

app = Flask(__name__)

app.register_blueprint(session_bp, url_prefix="/session")
app.register_blueprint(mount_bp, url_prefix="/mount")
#app.register_blueprint(hardware_bp, url_prefix="/hardware")
app.register_blueprint(hwcontroller_bp, url_prefix="/hwcontroller")


@app.before_request
def middleware():
    token = request.headers.get("Authorization")
    if token and SingletonSID().SID and token != str(SingletonSID().SID):
        return jsonify({"error": "session already acquired"}), 401
    if token and not SingletonSID().SID:
        return jsonify({"error": "no active session"}), 401
    if not token and request.path != "/session/acquire":
        return jsonify({"error": "unauthorized"}), 401


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000", debug=True)
