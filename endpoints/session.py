import uuid
from pathlib import Path
from flask import jsonify, Blueprint
from SingletonSID import SingletonSID

session_bp = Blueprint(Path(__file__).stem, __name__)


@session_bp.route("/acquire", methods=["GET"])
def session_acquire():
    if not SingletonSID().SID:
        SingletonSID().SID = uuid.uuid4()
        return jsonify({"session_id": SingletonSID().SID}), 200

    return jsonify({"message": "session in use"}), 403


@session_bp.route("/release", methods=["GET"])
def session_release():
    if SingletonSID().SID:
        SingletonSID().SID = None
        return jsonify({"message": "ok"}), 200

    return jsonify({"message": "cannot release an empty session"}), 403
