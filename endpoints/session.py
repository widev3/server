import uuid
from pathlib import Path
from flask import jsonify, Blueprint
from SessionProperties import SessionProperties as SP

session_bp = Blueprint(Path(__file__).stem, __name__)


@session_bp.route("/acquire", methods=["GET"])
def session_acquire():
    if not SP().SID:
        SP().SID = uuid.uuid4()

        print(
            f"[SESSION] Nuova sessione: SID={SP().SID} DEVICE={SP().DEVICE_ID} MOUNT={SP().MOUNT}"
        )

        return (
            jsonify(
                {
                    "session_id": str(SP().SID),
                    "device_id": SP().DEVICE_ID,
                    "mount_type": SP().MOUNT,
                }
            ),
            200,
        )

    return jsonify({"message": "session in use"}), 403


@session_bp.route("/release", methods=["GET"])
def session_release():
    if SP().SID:
        SP().SID = None
        SP().DEVICE_ID = None
        return jsonify({"message": "ok"}), 200

    return jsonify({"message": "cannot release an empty session"}), 403


@session_bp.route("/info", methods=["GET"])
def session_info():
    sid = SP().SID
    device = SP().DEVICE_ID

    if not sid:
        return jsonify({"session_id": None, "device_id": None, "status": "empty"}), 200

    return (
        jsonify({"session_id": str(sid), "device_id": device, "status": "active"}),
        200,
    )
