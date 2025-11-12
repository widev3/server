import uuid
from pathlib import Path
from flask import jsonify, Blueprint
from SingletonSID import SingletonSID

hardware_bp = Blueprint(Path(__file__).stem, __name__)

@hardware_bp.route("/", methods=["GET"])
def session_acquire():
    if not SingletonSID().SID:
        SingletonSID().SID = uuid.uuid4()
        return jsonify({"session_id": SingletonSID().SID}), 200

    return jsonify({"message": "session in use"}), 403
